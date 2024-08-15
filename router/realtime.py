import logging, asyncio
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    Query,
)
from entity.user import User as ODMUser
from entity.flow import Flow as ODMFlow
from service.credential import get_current_user, get_current_user_ws

from service.realtime import (
    depends_flow_realtime,
    depends_user_realtime,
    RealtimeFlowSession,
    RealtimeUserSession,
)
from service.websocket import ConnectionManager, depends_websocket_manager
from utils.flow import exist_node_in, update_dict_in_list, exist_edge_in

from utils.log import Logger

logger = Logger.create(__name__, level=logging.DEBUG)

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")


class Realtime:
    def __init__(
        self,
        rt_flow: RealtimeFlowSession,
        rt_user: RealtimeUserSession,
        connections: ConnectionManager,
    ):
        self.rt_flow = rt_flow
        self.rt_user = rt_user
        self.connections = connections

    @staticmethod
    @router.post("/join/{flow_id}")
    async def join_realtime(
        flow_id: str,
        current_user: ODMUser = Depends(get_current_user),
        rt_flow: RealtimeFlowSession = Depends(depends_flow_realtime),
        rt_user: RealtimeUserSession = Depends(depends_user_realtime),
        connections: ConnectionManager = Depends(depends_websocket_manager),
    ):
        realtime = Realtime(rt_flow, rt_user, connections)
        return await realtime._join_realtime(current_user, flow_id)

    async def _join_realtime(self, current_user: ODMUser, flow_id: str):
        odm_flow = await ODMFlow.get(flow_id)
        if odm_flow is None:
            raise HTTPException(status_code=404, detail="Flow not found")
        if not odm_flow.permission.get(str(current_user.id)):
            raise HTTPException(status_code=403, detail="Permission Denied")
        if not await self.rt_flow.exists(flow_id):
            print(odm_flow.model_dump())
            await self.rt_flow.update(flow_id, odm_flow.model_dump())
            user_realtime_data = {
                str(current_user.id): {
                    "database": current_user.model_dump(),
                    "position": {
                        "x": 0,
                        "y": 0,
                    },
                    "chat": "",
                }
            }
            await self.rt_user.update(flow_id, user_realtime_data)
        else:
            user_realtime_data = await self.rt_user.get(flow_id)
            if str(current_user.id) not in user_realtime_data:
                user_realtime_data[str(current_user.id)] = {
                    "database": current_user.model_dump(),
                    "position": {
                        "x": 0,
                        "y": 0,
                    },
                    "chat": "",
                }
                await self.rt_user.update(flow_id, user_realtime_data)

        export_data = odm_flow.model_dump()
        del export_data["permission"]
        del export_data["editor_option"]
        logger.info(f"User {current_user.username} joined realtime session({flow_id})")
        return {
            "message": "Joined Realtime Session",
            "data": export_data,
        }

    async def websocket_bg_worker(
        self, flow_id: str, odm_user: "ODMUser", worker_data: dict
    ):
        logger.info(
            f"User {odm_user.name}({str(odm_user.id)}) send data: {worker_data}"
        )
        if str(worker_data["op"]) == "3":
            logger.info(
                f"User {odm_user.name}({str(odm_user.id)}) send mouse move {worker_data['data']}"
            )
            await self.worker_mouse_move(flow_id, odm_user, worker_data["data"])
            mouse_move_data = await self.rt_user.get(flow_id)
            mouse_move_data[str(odm_user.id)]["position"] = worker_data["data"]
            await self.rt_user.update(flow_id, mouse_move_data)
            # position: {"x": 0, "y": 0}
        elif str(worker_data["op"]) == "4":
            logger.info(
                f"User {odm_user.name}({str(odm_user.id)}) change node {worker_data['data']}"
            )
            await self.worker_change_node(flow_id, odm_user, worker_data["data"])
            await self.node_redis_update(flow_id, worker_data["data"])
        elif str(worker_data["op"]) == "5":
            logger.info(
                f"User {odm_user.name}({str(odm_user.id)}) change edge {worker_data['data']}"
            )
            await self.worker_change_edge(flow_id, odm_user, worker_data["data"])
            await self.edge_redis_update(flow_id, worker_data["data"])
        elif str(worker_data["op"]) == "6":
            logger.info(
                f"User {odm_user.name}({str(odm_user.id)}) send chat {worker_data['data']['message']}"
            )
            await self.worker_user_chat(
                flow_id, odm_user, worker_data["data"]["message"]
            )
        else:
            ws_user_connection = self.connections.get(flow_id, str(odm_user.id))
            logger.info(
                f"User {odm_user.name}({str(odm_user.id)}) send invalid operation {worker_data}"
            )
            await ws_user_connection.send_json(
                {
                    "op": -3,
                    "data": {
                        "message": "Invalid Operation",
                        "error": "websocket.invalid.opcode",
                    },
                }
            )

    async def node_redis_update(self, flow_id: str, update_node_data: dict):
        flow_data = await self.rt_flow.get(flow_id)
        node_id: str = update_node_data["id"]
        logger.info(f"Redis Flow Data edit requested: {flow_id} {update_node_data}")
        if not exist_node_in(flow_data, node_id):
            flow_data["nodes"].append(update_node_data)
            return await self.rt_flow.update(flow_id, flow_data)

        if update_node_data.get("data"):
            flow_data["nodes"] = update_dict_in_list(
                flow_data["nodes"], node_id, update_node_data["data"], "data"
            )

        if update_node_data.get("position"):
            flow_data["nodes"] = update_dict_in_list(
                flow_data["nodes"], node_id, update_node_data["position"], "position"
            )

        if update_node_data.get("measured"):
            flow_data["nodes"] = update_dict_in_list(
                flow_data["nodes"], node_id, update_node_data["measured"], "measured"
            )

        await self.rt_flow.update(flow_id, flow_data)

    async def edge_redis_update(self, flow_id: str, update_edge_data: dict):
        flow_data = await self.rt_flow.get(flow_id)
        edge_id: str = update_edge_data["id"]
        if not exist_edge_in(flow_data, edge_id):
            flow_data["edges"].append(update_edge_data)
            return

        flow_data["edges"] = update_dict_in_list(
            flow_data["edges"], edge_id, update_edge_data
        )

        await self.rt_flow.update(flow_id, flow_data)

    async def worker_join_user(self, flow_id: str, odm_user: "ODMUser") -> None:
        await self.connections.broadcast(
            flow_id,
            {
                "op": 1,
                "data": {
                    "uid": str(odm_user.id),
                    "name": odm_user.username,
                    "username": odm_user.username,
                    "profile_url": odm_user.profile_url,
                },
            },
        )

    async def worker_leave_user(self, flow_id: str, odm_user: "ODMUser") -> None:
        room = await self.rt_user.get(flow_id)
        del room[str(odm_user.id)]
        if len(room.keys()) == 0:
            await self.rt_user.delete(flow_id)
            redis_flow_data = await self.rt_flow.get(flow_id)
            odm_flow_model = await ODMFlow.get(flow_id)
            await odm_flow_model.update({"$set": redis_flow_data})
            await self.rt_flow.delete(flow_id)

        await self.connections.broadcast(
            flow_id,
            {
                "op": 2,
                "data": {
                    "uid": str(odm_user.id),
                    "username": odm_user.username,
                    "profile_url": odm_user.profile_url,
                },
            },
        )

    async def worker_mouse_move(
        self, flow_id: str, odm_user: "ODMUser", position: dict
    ) -> None:
        """
        ReactFlow, XYPosition Type
        comment: 마우스 이동값 X, UserMouseNode라는 노드의 position 정보

        export type XYPosition = {
          x: number;
          y: number;
        };
        """
        await self.connections.broadcast(
            flow_id,
            {
                "op": 3,
                "data": {
                    "uid": str(odm_user.id),
                    "position": position,
                },
            },
        )

    async def worker_change_node(
        self, flow_id: str, odm_user: "ODMUser", node_data: dict
    ) -> None:
        await self.connections.broadcast(
            flow_id,
            {
                "op": 4,
                "data": {
                    "uid": str(odm_user.id),
                    "node": node_data,
                },
            },
        )

    async def worker_change_edge(
        self, flow_id: str, odm_user: "ODMUser", flow_data: dict
    ) -> None:
        await self.connections.broadcast(
            flow_id,
            {
                "op": 5,
                "data": {
                    "uid": str(odm_user.id),
                    "flow": flow_data,
                },
            },
        )

    async def worker_user_chat(
        self, flow_id: str, odm_user: "ODMUser", message: str
    ) -> None:
        await self.connections.broadcast(
            flow_id,
            {
                "op": 6,
                "data": {
                    "uid": str(odm_user.id),
                    "message": message,
                },
            },
        )


@router.websocket("/{flow_id}")
async def realtime_endpoint(
    websocket: WebSocket,
    background_tasks: BackgroundTasks,
    flow_id: str,
    token: str = Query(...),
    rt_flow: RealtimeFlowSession = Depends(depends_flow_realtime),
    rt_user: RealtimeUserSession = Depends(depends_user_realtime),
    connections: ConnectionManager = Depends(depends_websocket_manager),
):
    logger.info(f"New Realtime Connection: {flow_id}, ip: {websocket.client.host}")
    await websocket.accept()
    current_user = await get_current_user_ws(token, websocket)
    if current_user is None:
        return await websocket.close()
    realtime_instance = Realtime(rt_flow, rt_user, connections)
    odm_flow = await ODMFlow.get(flow_id)
    if odm_flow is None:
        await websocket.send_json({"op": -3, "msg": "Flow not found"})
        return await websocket.close()
    try:
        session_users = await rt_user.get(flow_id)
    except TypeError:
        await websocket.send_json({"op": -3, "msg": "Session not found"})
        return await websocket.close()
    if not session_users or str(current_user.id) not in session_users.keys():
        await websocket.send_json({"op": -3, "msg": "Flow not found"})
        return await websocket.close()
    await connections.connect(flow_id, str(current_user.id), websocket)
    await realtime_instance.worker_join_user(flow_id, current_user)
    is_in_recent = False
    for recent_flows in current_user.recent:
        if recent_flows["id"] == flow_id:
            is_in_recent = True
    if not is_in_recent:
        current_user.recent.append({"id": flow_id, "name": odm_flow.name})
        await current_user.save()
    try:
        await websocket.send_json({"op": 0, "msg": "Connected"})
        while True:
            received_data = await websocket.receive_json()
            logger.info(
                f"User {current_user.name}({str(current_user.id)}) send data: {received_data}"
            )
            background_tasks.add_task(
                realtime_instance.websocket_bg_worker,
                flow_id=flow_id,
                odm_user=current_user,
                worker_data=received_data,
            )
            await asyncio.create_task(
                realtime_instance.websocket_bg_worker(
                    flow_id, current_user, received_data
                )
            )
    except WebSocketDisconnect:
        await realtime_instance.worker_leave_user(flow_id, current_user)
        connections.disconnect(flow_id, str(current_user.id))

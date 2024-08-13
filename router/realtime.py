from fastapi_restful.cbv import cbv
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Body,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
)

from entity.user import User as ODMUser
from entity.flow import Flow as ODMFlow
from entity.internal.frontend import FrontendModal, FrontendAction
from service.credential import get_current_user

from service.realtime import (
    depends_flow_realtime,
    depends_user_realtime,
    RealtimeFlowSession,
    RealtimeUserSession,
)
from service.websocket import ConnectionManager, depends_websocket_manager
from utils.flow import exist_node_in, update_dict_in_list, exist_edge_in

router = APIRouter(
    prefix="/realtime",
    tags=["realtime"],
)


@cbv(router)
class Realtime:
    rt_flow: RealtimeFlowSession = Depends(depends_flow_realtime)
    rt_user: RealtimeUserSession = Depends(depends_user_realtime)
    connections: ConnectionManager = Depends(depends_websocket_manager)

    @router.websocket("/{flow_id}")
    async def realtime_endpoint(
        self,
        websocket: WebSocket,
        background_tasks: BackgroundTasks,
        flow_id: str,
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        odm_flow = await ODMFlow.find({"id": flow_id}).first_or_none()
        if odm_flow is None:
            raise HTTPException(status_code=404, detail="Flow not found")
        session_users = await self.rt_user.get(flow_id)
        if not session_users or current_user.id not in session_users:
            raise HTTPException(status_code=403, detail="Permission Denied")

        await self.connections.connect(flow_id, str(current_user.id), websocket)
        try:
            await websocket.send_json({"op": 0})
            while True:
                received_data = await websocket.receive_json()
                background_tasks.add_task(self.websocket_bg_worker, flow_id, current_user, received_data)
        except WebSocketDisconnect:
            await self.worker_leave_user(flow_id, current_user)
            self.connections.disconnect(flow_id, str(current_user.id))

    async def websocket_bg_worker(
        self, flow_id: str, odm_user: "ODMUser", worker_data: dict
    ):
        if str(worker_data["op"]) == "3":
            await self.worker_mouse_move(flow_id, odm_user, worker_data["data"])
            mouse_move_data = await self.rt_user.get(flow_id)
            mouse_move_data[odm_user.id]["position"] = worker_data["data"]
            await self.rt_user.update(flow_id, mouse_move_data)
            # position: {"x": 0, "y": 0}
        elif str(worker_data["op"]) == "4":
            await self.worker_change_node(flow_id, odm_user, worker_data["data"])
            await self.node_redis_update(flow_id, worker_data["data"])
        elif str(worker_data["op"]) == "5":
            await self.worker_change_edge(flow_id, odm_user, worker_data["data"])
            await self.edge_redis_update(flow_id, worker_data["data"])
        elif str(worker_data["op"]) == "6":
            await self.worker_user_chat(flow_id, odm_user, worker_data["data"]["message"])
        else:
            ws_user_connection = self.connections.get(flow_id, str(odm_user.id))
            await ws_user_connection.send_json(
                {"op": -3, "data": {
                    "message": "Invalid Operation",
                    "error": "websocket.invalid.opcode"
                }}
            )

    async def node_redis_update(self, flow_id: str, update_node_data: dict):
        flow_data = await self.rt_flow.get(flow_id)
        node_id: str = update_node_data["id"]
        if not exist_node_in(flow_data, node_id):
            flow_data["nodes"].append(update_node_data)
            return

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
                    "uid": odm_user.id,
                    "name": odm_user.username,
                    "username": odm_user.username,
                    "profile_url": odm_user.profile_url,
                },
            },
        )

    async def worker_leave_user(self, flow_id: str, odm_user: "ODMUser") -> None:
        await self.connections.broadcast(
            flow_id,
            {
                "op": 2,
                "data": {
                    "uid": odm_user.id,
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
                    "uid": odm_user.id,
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
                    "uid": odm_user.id,
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
                    "uid": odm_user.id,
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
                    "uid": odm_user.id,
                    "message": message,
                },
            },
        )

    @router.post("/join")
    async def join_realtime(
        self,
        current_user: "ODMUser" = Depends(get_current_user),
        flow_id: str = Body(
            title="Flow ID",
            description="Realtime 방에 참가할 Flow ID",
        ),
    ):
        odm_flow = await ODMFlow.find({"id": flow_id}).first_or_none()
        if odm_flow is None:
            raise HTTPException(status_code=404, detail="Flow not found")
        if not odm_flow.permission.get(str(current_user.id)):
            raise HTTPException(status_code=403, detail="Permission Denied")
        if not await self.rt_flow.exists(flow_id):
            await self.rt_flow.update(flow_id, odm_flow.model_dump())
            user_realtime_data = {
                current_user.id: {
                    "database": current_user.model_dump(),
                    "position": {
                        "x": 0,
                        "y": 0,
                    },
                    "chat": None,
                }
            }
            await self.rt_user.update(flow_id, user_realtime_data)
        else:
            user_realtime_data = await self.rt_user.get(flow_id)
            if current_user.id not in user_realtime_data:
                user_realtime_data[current_user.id] = {
                    "database": current_user.model_dump(),
                    "position": {
                        "x": 0,
                        "y": 0,
                    },
                    "chat": None,
                }
                await self.rt_user.update(flow_id, user_realtime_data)
        await self.worker_join_user(flow_id, current_user)

        export_data = odm_flow.model_dump()
        del export_data["permission"]
        del export_data["editor_option"]
        return {
            "message": "Joined Realtime Session",
            "data": export_data,
        }

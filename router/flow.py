import logging, uuid
from fastapi import APIRouter, Depends, status, Query
from fastapi_restful.cbv import cbv
from entity.user import User as ODMUser
from entity.flow import Flow as ModelFlow, Node
from service.liveblock import liveblock
from service.credential import get_current_user
from utils.log import Logger

logger = Logger.create(__name__, level=logging.DEBUG)

router = APIRouter(
    prefix="/flows",
    tags=["Flows"],
)


@cbv(router)
class Flow:
    @router.post("/", status_code=status.HTTP_201_CREATED)
    async def create_flow(
        self,
        prompt: str,
        user: "ODMUser" = Depends(get_current_user),
    ):
        create_flow_model = ModelFlow(
            nodes=[
                Node(
                    id="system@start",
                    type="aiStartupNode",
                    measured={},
                    position={"x": 0, "y": 0},
                    data={
                        "text": prompt,
                        "isAllowEditing": True,
                    },
                    selected=True,
                    dragging=True,
                )
            ],
            edges=[],
        )
        await liveblock.create_room(
            room_id=create_flow_model.id,
            default_permission=[],
            user_permission={str(user.id): "owner"},
            metadata={
                "owner_id": str(user.id),
                "owner_name": user.name,
                "owner_profile_url": user.profile_url,
                "start_message": prompt,
                "viewers": 0,
            },
        )
        await liveblock.set_document(
            room_id=create_flow_model.id,
            document=create_flow_model.model_dump(),
        )
        logger.info(f"Create flow: {str(create_flow_model.id)}")
        return {"message": "Create flow", "data": str(create_flow_model.id)}

    @router.get("/community")
    async def get_community_flows(
        self,
        limit: int = Query(..., ge=1, le=100),
        query: str = Query(None),
    ):
        kwargs_data = {"limit": limit, "groupIds": ["community"]}
        if query:
            kwargs_data["query"] = query
        result = await liveblock.search_rooms(**kwargs_data)
        return_data = []
        for flow in result.data.values():
            return_data.append(
                {
                    "id": str(flow.id),
                    "name": flow["metadata"]["start_message"],
                    "author_name": flow["metadata"]["owner_name"],
                    "author_profile_url": flow["metadata"]["owner_profile_url"],
                    "viewers": flow["metadata"]["viewers"],
                }
            )
        return {
            "message": "Community flows",
            "data": return_data,
        }

    @router.get("/recommend")
    async def get_recommend_prompt(
        self,
        _user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Recommend prompt",
            "data": [
                "python으로 자율주행 자동차 만들기",
                "파이썬으로 머신러닝 공부하기",
                "javascript로 실시간 채팅 웹사이트 만들기",
            ],
        }

    @router.get("/")
    async def get_my_project_flows(
        self,
        user: "ODMUser" = Depends(get_current_user),
    ):
        result = await liveblock.search_rooms(
            userId=str(user.id),
        )
        return_data = []
        for flow in result.data.values():
            return_data.append(
                {
                    "id": str(flow.id),
                    "name": flow["metadata"]["start_message"],
                }
            )
        return {
            "message": "Project flows",
            "data": return_data,
        }

    @router.get("/recent")
    async def get_recent_flows(
        self,
        user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Recent flows",
            "data": user.recent[::-1],
        }

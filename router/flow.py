import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi_restful.cbv import cbv
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from entity.flow import Flow as ODMFlow, FlowUserPermission, Node, Edge, EditorOption
from entity.user import User as ODMUser
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
        create_flow_model = ODMFlow(
            permission={str(user.id): FlowUserPermission(permission=["owner"])},
            nodes=[
                Node(
                    id="system@start",
                    type="aiStartupNode",
                    measured={},
                    position={"x": 0, "y": 0},
                    data={
                        "text": prompt,
                    },
                    selected=True,
                    dragging=True,
                )
            ],
            edges=[],
            editor_option={
                str(user.id): EditorOption(viewport={"x": 0, "y": 0}),
            },
        )
        await create_flow_model.insert()
        return {"message": "Create flow", "data": {"id": str(create_flow_model.id)}}

    @router.get("/recommend")
    async def get_recommend_prompt(
        self,
        _user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Recommend prompt",
            "data": [
                "What is the best way to learn programming?",
                "What is the best way to learn programming?",
                "What is the best way to learn programming?",
            ],
        }

    @router.get("/")
    async def get_project_flows(
        self,
        _user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Project flows",
            "data": [
                {
                    "id": "flow_id",
                    "name": "flow_name",
                }
            ],
        }

    @router.get("/recent")
    async def get_recent_flows(
        self,
        _user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Recent flows",
            "data": [
                {
                    "id": "flow_id",
                    "name": "flow_name",
                }
            ],
        }

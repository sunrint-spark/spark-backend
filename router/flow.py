import logging
from fastapi import APIRouter, Depends, status
from fastapi_restful.cbv import cbv
from entity.flow import Flow as ODMFlow, Node, EditorOption
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
            permission={str(user.id): ["owner"]},
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
        await create_flow_model.create()
        logger.info(f"Create flow: {str(create_flow_model.id)}")
        return {"message": "Create flow", "data": str(create_flow_model.id)}

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
    async def get_project_flows(
        self,
        user: "ODMUser" = Depends(get_current_user),
    ):
        result = await ODMFlow.find(
            {f"permission.{str(user.id)}": {"$exists": True}}
        ).to_list()
        return_data = []
        for flow in result:
            return_data.append(
                {
                    "id": str(flow.id),
                    "name": flow.nodes[0].data["text"],
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
            "data": user.recent,
        }

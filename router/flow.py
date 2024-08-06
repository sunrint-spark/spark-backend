import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi_restful.cbv import cbv
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from entity.flow import Flow
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
    @router.post("/", response_model=Flow, status_code=status.HTTP_201_CREATED)
    async def create_flow(
        self, flow: Flow, user: "ODMUser" = Depends(get_current_user),
    ):
        try:
            await flow.create()
            return flow
        except Exception as e:
            # 예외 처리 및 로깅
            logger.error(f"Error creating flow[user:{user.id}]: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
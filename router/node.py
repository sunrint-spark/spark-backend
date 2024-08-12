import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi_restful.cbv import cbv
from entity.flow import Node as FlowNode
from entity.user import User as ODMUser
from service.credential import get_current_user
from utils.log import Logger

logger = Logger.create(__name__, level=logging.DEBUG)

router = APIRouter(
    prefix="/save",
    tags=["Node"],
)

@cbv(router)
class Node:
    @router.post("/", response_model=FlowNode, status_code=status.HTTP_201_CREATED)
    async def create_node(
        self, node: FlowNode, user: ODMUser = Depends(get_current_user),
    ):
        try:
            await node.create()
            return node
        except Exception as e:
            logger.error(f"Error creating node[user:{user.id}]: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
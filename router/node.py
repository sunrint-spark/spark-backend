import logging
import time
import redis
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi_restful.cbv import cbv
from entity.flow import Node as FlowNode
from entity.user import User as ODMUser
from service.credential import get_current_user
from utils.log import Logger
import pymongo
import os
import json

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PASSWORD")
)

logger = Logger.create(__name__, level=logging.DEBUG)

pymongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = pymongo_client[os.getenv("MONGO_DB")]
collection = db[os.getenv("MONGO_COLLECTION")]

router = APIRouter(
    prefix="/save",
    tags=["Node"],
)

@cbv(router)
class Node:
    def __init__(self):
        self.last_hello_time = time.time()

    @router.post("/", response_model=FlowNode, status_code=status.HTTP_201_CREATED)
    async def save_node_position(
        self, node: FlowNode, user: ODMUser = Depends(get_current_user), node_position: dict[str, int] = None
    ):
        try:
            node_id = str(node.id)
            await redis_client.set(node_id, node.json())
            return node
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                if data == "HELLO":
                    self.last_hello_time = time.time()
                else:
                    node_data = json.loads(data)
                    node_id = str(node_data["id"])
                    await redis_client.set(node_id, json.dumps(node_data))
                await self.db_save_node()
        except WebSocketDisconnect:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def db_save_node(self):
        current_time = time.time()
        if current_time - self.last_hello_time > 1:
            try:
                all_keys = redis_client.keys("*")
                for key in all_keys:
                    node_data = redis_client.get(key)
                    if node_data:
                        node_dict = json.loads(node_data)
                        collection.update_one(
                            {"_id": node_dict["id"]},
                            {"$set": node_dict},
                            upsert=True
                        )
                        logger.info(f"Node {node_dict['id']} saved to database")
                # Clear Redis after saving all nodes
                await redis_client.flushdb()
                logger.info("All nodes saved to database and Redis cleared")
            except Exception as e:
                logger.error(f"Error saving nodes to database: {e}")
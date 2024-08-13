from fastapi import WebSocket
from service.credential import get_redis_pool


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}
        self.redis_connection = get_redis_pool()

    async def connect(self, flow_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if not self.active_connections.get(flow_id):
            self.active_connections[flow_id] = {}
        self.active_connections[flow_id][user_id] = websocket

    def disconnect(self, flow_id: str, user_id: str):
        del self.active_connections[flow_id][user_id]

    def get(self, flow_id: str, user_id: str) -> WebSocket:
        return self.active_connections[flow_id][user_id]

    async def broadcast(self, flow_id: str, data: dict):
        for connection in self.active_connections[flow_id].values():
            try:
                await connection.send_json(data)
            except Exception as e:
                pass


async def depends_websocket_manager():
    return ConnectionManager()

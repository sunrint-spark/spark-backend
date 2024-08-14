from fastapi import WebSocket
from service.credential import get_redis_pool


class ConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections = {}
            cls._instance.redis_connection = get_redis_pool()
        return cls._instance

    async def connect(self, flow_id: str, user_id: str, websocket: WebSocket):
        if flow_id not in self.active_connections:
            self.active_connections[flow_id] = {}
        self.active_connections[flow_id][user_id] = websocket

    def disconnect(self, flow_id: str, user_id: str):
        if (
            flow_id in self.active_connections
            and user_id in self.active_connections[flow_id]
        ):
            del self.active_connections[flow_id][user_id]
            if not self.active_connections[flow_id]:
                del self.active_connections[flow_id]

    def get(self, flow_id: str, user_id: str) -> WebSocket:
        return self.active_connections.get(flow_id, {}).get(user_id)

    async def broadcast(self, flow_id: str, data: dict):
        if flow_id in self.active_connections:
            for connection in self.active_connections[flow_id].values():
                try:
                    await connection.send_json(data)
                except Exception as e:
                    print(f"Broadcasting error: {e}")


connection_manager = ConnectionManager()


def depends_websocket_manager():
    return connection_manager

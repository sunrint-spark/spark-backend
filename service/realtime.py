import json

from service.credential import get_redis_pool


class RealtimeUserSession:
    def __init__(self):
        self.redis_connection = get_redis_pool()

    async def update(self, flow_id: str, data: dict) -> None:
        await self.redis_connection.hset("realtime", flow_id, json.dumps(data))

    async def get(self, flow_id: str) -> dict:
        data = await self.redis_connection.hget("realtime", flow_id)
        return json.loads(data)

    async def delete(self, flow_id: str) -> None:
        await self.redis_connection.hdel("realtime", flow_id)

    async def exists(self, flow_id: str) -> bool:
        return await self.redis_connection.hexists("realtime", flow_id)


async def depends_user_realtime():
    return RealtimeUserSession()

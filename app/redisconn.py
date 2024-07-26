import redis.asyncio as redis


class RedisConn:
    def __init__(self, host: str, port: int, db: int):
        self._pool = redis.ConnectionPool(host=host, port=port, db=db)

    @property
    def connection(self):
        return redis.Redis(connection_pool=self._pool)

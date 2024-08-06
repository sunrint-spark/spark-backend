import json

from service.credential import get_redis_pool
from datetime import timedelta

from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(
    scheme_name="User Access Token",
    description="/auth에서 발급받은 토큰을 입력해주세요",
)


class Session:
    def __init__(self, token: str):
        self.token = token
        self.redis_connection = get_redis_pool()

    async def set_expire(self, expire: timedelta) -> None:
        session_key = "SessionToken" + self.token
        await self.redis_connection.expire(session_key, expire)

    async def update(self, data: dict) -> None:
        session_key = "SessionToken" + self.token
        await self.redis_connection.hset("session", session_key, json.dumps(data))

    async def get(self) -> dict:
        session_key = "SessionToken" + self.token
        data = await self.redis_connection.hget("session", session_key)
        return json.loads(data)

    async def delete(self) -> None:
        session_key = "SessionToken" + self.token
        await self.redis_connection.hdel("session", session_key)

    async def is_valid(self) -> bool:
        session_key = "SessionToken" + self.token
        return await self.redis_connection.hexists("session", session_key)


async def get_active_session(
    authorization: HTTPAuthorizationCredentials = Security(security),
) -> Session:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    session = Session(token=authorization.credentials)
    if await session.is_valid():
        return session
    else:
        raise credentials_exception

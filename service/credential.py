import os
import jwt

from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.testmode import get_or_create_test_user, TEST_USER_ACCESS_TOKEN
from app.redisconn import RedisConn
from entity.user import User as ODMUser

security = HTTPBearer(
    scheme_name="access_token",
    description="/auth에서 발급받은 토큰을 입력해주세요",
)


def get_redis_pool():
    redis_pool = RedisConn(
        host=os.environ["REDIS_HOST"], port=int(os.environ["REDIS_PORT"]), db=0
    )
    return redis_pool.connection


class Credential:
    def __init__(self):
        self.redis_connection = get_redis_pool()

    @staticmethod
    def verify_password(
        password_context: CryptContext, plain_password: str, hashed_password: str
    ):
        return password_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(cls, password):
        return cls.password_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_token = jwt.encode(
            to_encode, os.environ["JWT_SECRET_KEY"], algorithm="HS256"
        )
        return encoded_token

    async def register_token(self, expire: timedelta, user_id: str, token: str):
        await self.redis_connection.hset("user", token, user_id)
        await self.redis_connection.expire(token, expire)

    async def delete_token(self, token: str):
        await self.redis_connection.hdel("user", token)

    async def is_valid_token(self, token: str):
        return await self.redis_connection.hexists("user", token)


async def depends_credential():
    return Credential()


async def get_current_user(
    credential: Credential = Depends(depends_credential),
    authorization: HTTPAuthorizationCredentials = Security(security),
) -> ODMUser:
    session_token = authorization.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if os.getenv("TEST_MODE") == "true":
        if session_token == TEST_USER_ACCESS_TOKEN:
            return await get_or_create_test_user()
    try:
        payload = jwt.decode(
            session_token, os.environ["JWT_SECRET_KEY"], algorithms=["HS256"]
        )
        user_document_id: str | None = payload.get("sub")
        if user_document_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    if not await credential.is_valid_token(token=session_token):
        raise credentials_exception
    odm_user = await ODMUser.get(document_id=user_document_id)
    if odm_user is None:
        raise credentials_exception
    return odm_user

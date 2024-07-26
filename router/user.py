from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from passlib.context import CryptContext

router = APIRouter()


@cbv(router)
class Home:
    @router.get("/home")
    async def root(self):
        return {"message": "Hello Home"}

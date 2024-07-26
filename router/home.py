from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv

router = APIRouter()


@cbv(router)
class Home:
    @router.get("/home")
    async def root(self):
        return {"message": "Hello Home"}

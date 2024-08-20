import logging
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_restful.cbv import cbv
from entity.user import User as ODMUser
from service.liveblock import liveblock
from service.credential import get_current_user
from utils.log import Logger
from pydantic import BaseModel

logger = Logger.create(__name__, level=logging.DEBUG)

router = APIRouter(
    prefix="/realtime",
    tags=["Liveblock Realtime"],
)


class InviteUser(BaseModel):
    email: str
    permission: Literal["write", "read"]


@cbv(router)
class Flow:

    @router.get("/{flow_id}/join")
    async def join_realtime(
        self,
        flow_id: str,
        community: bool = Query(False),
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        fetch_room_data = await liveblock.fetch_room(flow_id)
        if fetch_room_data.get("error") == "ROOM_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Flow not found")
        if community:
            if fetch_room_data.groupAccesses.get("community") is None:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "COMMUNITY_PERMISSION_DENIED",
                        "message": "Permission Denied",
                    },
                )
            liveblock_access_token = await liveblock.create_token(
                odm_user=current_user, groups=["community"]
            )
            logger.info(
                f"User {current_user.username} joined realtime session({flow_id}.community)"
            )
            return {
                "message": "Joined Realtime Session",
                "data": {
                    "access_token": liveblock_access_token["token"],
                    "permission": "room:read",
                },
            }
        else:
            if fetch_room_data["usersAccesses"].get(str(current_user.id)) is None:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "PERMISSION_DENIED",
                        "message": "Permission Denied",
                    },
                )
            liveblock_access_token = await liveblock.create_token(odm_user=current_user)
            logger.info(
                f"User {current_user.username} joined realtime session({flow_id}.private)"
            )
            return {
                "message": "Joined Realtime Session",
                "data": {
                    "access_token": liveblock_access_token["token"],
                    "permission": fetch_room_data["usersAccesses"].get(
                        str(current_user.id)
                    ),
                },
            }

    @router.get("/user")
    async def query_user_by_email(self, email: str = Query(...)):
        target_user = await ODMUser.find({"email": email}).first_or_none()
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail={"error": "USER_NOT_FOUND", "message": "User not found"},
            )
        return {
            "code": "USER_FOUND",
            "message": "User found",
            "data": {
                "user_name": target_user.name,
                "user_profile_url": target_user.profile_url,
                "user_id": str(target_user.id),
            },
        }

    @router.post("/{flow_id}/publish")
    async def publish_flow(
        self,
        flow_id: str,
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        fetch_room_data = await liveblock.fetch_room(flow_id)
        if fetch_room_data.get("error") == "ROOM_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "FLOW_NOT_FOUND", "message": "Flow not found"},
            )
        if not fetch_room_data["metadata"].get("owner_id") == str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail={"error": "PERMISSION_DENIED", "message": "Permission Denied"},
            )
        fetch_room_data.groupAccesses["community"] = "room:read"
        await liveblock.update_room(
            room_id=flow_id, groupAccesses=fetch_room_data.groupAccesses
        )
        return {"code": "DOCUMENT_PUBLISHED", "message": "Document published"}

    @router.get("/{flow_id}/invite")
    async def get_invite_list(
        self,
        flow_id: str,
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        fetch_room_data = await liveblock.fetch_room(flow_id)
        if fetch_room_data.get("error") == "ROOM_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "FLOW_NOT_FOUND", "message": "Flow not found"},
            )
        if fetch_room_data.usersAccesses.get(str(current_user.id)) is None:
            raise HTTPException(
                status_code=403,
                detail={"error": "PERMISSION_DENIED", "message": "Permission Denied"},
            )
        invite_list = []
        for user_id, permission in fetch_room_data["usersAccesses"].items():
            if user_id != str(current_user.id):
                user = await ODMUser.get(document_id=user_id)
                invite_list.append(
                    {
                        "user_name": user.name,
                        "user_profile_url": user.profile_url,
                        "user_id": str(user.id),
                        "permission": permission,
                    }
                )
        return {
            "code": "INVITE_LIST",
            "message": "Invite list",
            "data": invite_list,
        }

    @router.post("/{flow_id}/invite")
    async def invite_user(
        self,
        flow_id: str,
        invite_user: InviteUser,
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        fetch_room_data = await liveblock.fetch_room(flow_id)
        if fetch_room_data.get("error") == "ROOM_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "FLOW_NOT_FOUND", "message": "Flow not found"},
            )
        if fetch_room_data.usersAccesses.get(str(current_user.id)) is None:
            raise HTTPException(
                status_code=403,
                detail={"error": "PERMISSION_DENIED", "message": "Permission Denied"},
            )
        target_user = await ODMUser.find({"email": invite_user.email}).first_or_none()
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail={"error": "USER_NOT_FOUND", "message": "User not found"},
            )
        fetch_room_data["usersAccesses"][
            str(target_user.id)
        ] = f"room:{invite_user.permission}"
        await liveblock.update_room(
            flow_id,
            defaultAccesses=fetch_room_data["defaultAccesses"],
            groupAccesses=fetch_room_data["groupAccesses"],
            userAccesses=fetch_room_data["usersAccesses"],
        )
        return {
            "code": "PERMISSION_UPDATED",
            "message": "User permission updated",
            "data": {
                "user_name": target_user.name,
                "user_profile_url": target_user.profile_url,
                "user_id": str(target_user.id),
                "permission": invite_user.permission,
            },
        }

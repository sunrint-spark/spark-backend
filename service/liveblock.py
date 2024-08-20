import os
from aiohttp import ClientSession
from utils.request import BaseRequest
from entity.user import User as ODMuser

LIVEBLOCK_SECRET_KEY = os.getenv("LIVEBLOCK_SECRET_KEY")


class LiveBlock(BaseRequest):
    def __init__(self):
        super().__init__()

    async def create_token(self, odm_user: ODMuser, groups: list[str] = None) -> dict:
        request_data = {
            "userId": str(odm_user.id),
            "groupIds": groups or [],
            "userInfo": {
                "name": odm_user.name,
                "email": odm_user.email,
                "avatar": odm_user.profile_url,
            },
        }
        response = await self.post(
            "https://api.liveblocks.io/v2/identify-user",
            json=request_data,
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def search_rooms(self, **params) -> dict:
        response = await self.get(
            "https://api.liveblocks.io/v2/rooms",
            params=params,
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def fetch_room(self, room_id: str) -> dict:
        response = await self.get(
            f"https://api.liveblocks.io/v2/rooms/{room_id}",
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def fetch_active_users(self, room_id: str) -> dict:
        response = await self.get(
            f"https://api.liveblocks.io/v2/rooms/{room_id}/active_users",
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def update_room(self, room_id: str, **data) -> dict:
        response = await self.post(
            f"https://api.liveblocks.io/v2/rooms/{room_id}",
            json=data,
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def create_room(
        self,
        room_id: str,
        default_permission: list[str],
        user_permission: dict[str, str],
        metadata: dict | None,
    ) -> dict:
        request_data = {
            "id": room_id,
            "defaultAccesses": default_permission,
            "metadata": metadata or {},
            "usersAccesses": user_permission,
            "groupsAccesses": {},
        }
        response = await self.post(
            "https://api.liveblocks.io/v2/rooms",
            json=request_data,
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def set_document(self, room_id: str, document: dict) -> dict:
        response = await self.post(
            f"https://api.liveblocks.io/rooms/{room_id}/storage",
            json={
                "liveblocksType": "LiveObject",
                "data": document,
            },
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()

    async def broadcast(self, room_id: str, data: dict) -> dict:
        response = await self.post(
            f"https://api.liveblocks.io/v2/rooms/{room_id}/broadcast_event",
            json=data,
            headers={"Authorization": "Bearer " + LIVEBLOCK_SECRET_KEY},
        )
        return await response.json()


liveblock = LiveBlock()

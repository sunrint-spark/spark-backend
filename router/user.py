import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

import traceback
from fastapi import APIRouter, HTTPException, Depends, Body, Request
from fastapi.responses import RedirectResponse
from fastapi_restful.cbv import cbv
from passlib.context import CryptContext

from entity.user import User as ODMUser
from aiogoogle import Aiogoogle, auth as aiogoogle_auth

from service.credential import depends_credential, Credential, get_current_user
from service.session import Session, get_active_session

load_dotenv(verbose=True)
router = APIRouter(prefix="/user", tags=["user"])

GOOGLE_CLIENT_CREDS = aiogoogle_auth.creds.ClientCreds(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scopes=["profile", "email"],
    redirect_uri="http://localhost:5173/callback",
)
GOOGLE_STATE = os.urandom(10).hex()
print(GOOGLE_STATE)


@cbv(router)
class User:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    credential: Credential = Depends(depends_credential)
    google_oauth = Aiogoogle(
        client_creds=GOOGLE_CLIENT_CREDS,
    )

    @router.get("/authorization_url")
    async def get_authorization_url(self):
        return RedirectResponse(
            url=self.google_oauth.oauth2.authorization_url(
                client_creds=GOOGLE_CLIENT_CREDS,
                state=GOOGLE_STATE,
                access_type="online",
                include_granted_scopes=True,
                prompt="select_account",
            )
        )

    @router.post(
        "/auth",
        summary="Google OAuth2.0 인증을 통해 사용자를 인증합니다.",
        description="Google OAuth2.0 인증을 통해 사용자를 인증합니다.\n"
        "회원가입이 되어 있지 않으면 자동으로 회원가입 후, 로그인합니다.",
    )
    async def auth(
        self,
        state: str = Body(
            title="state", description="/authorization_url 로부터 받은 state 값"
        ),
        code: str = Body(
            title="Google Oauth Callback Code",
            description="Google OAuth2.0 Callback에서 받은 code 값",
        ),
    ):
        if state != GOOGLE_STATE:
            raise HTTPException(status_code=400, detail="Invalid State")
        user_creds = await self.google_oauth.oauth2.build_user_creds(
            grant=code, client_creds=GOOGLE_CLIENT_CREDS
        )
        userinfo = await self.google_oauth.oauth2.get_me_info(user_creds=user_creds)
        odm_user = await ODMUser.find({"email": userinfo["email"]}).first_or_none()
        if not odm_user:
            odm_user = ODMUser(
                name=userinfo["name"],
                username=userinfo["email"].split("@")[0],
                email=userinfo["email"],
                profile_url=userinfo["picture"],
            )
            odm_user = await odm_user.create()
        access_token_expires = timedelta(days=10)
        access_token = self.credential.create_access_token(
            data={"sub": str(odm_user.id)}, expires_delta=access_token_expires
        )
        try:
            await self.credential.register_token(
                expire=access_token_expires,
                token=access_token,
                user_id=str(odm_user.id),
            )
            token_expired_time = datetime.now() + access_token_expires
            session = Session(token=access_token)
            await session.set_expire(access_token_expires)
            await session.update({})

            return {
                "message": "Login Success",
                "token": access_token,
                "expired": int(token_expired_time.timestamp()),
            }
        except Exception as e:
            traceback.print_exception(e)
            raise HTTPException(
                status_code=500, detail="Internal Server Error, " + str(e)
            )

    @router.post("/logout", description="로그아웃하기 (토큰 만료시키기)")
    async def logout(
        self,
        request: Request,
        _current_user: "ODMUser" = Depends(get_current_user),
    ):
        token = request.headers["Authorization"].split(" ")[1]
        await self.credential.delete_token(token=token)
        return {
            "message": "Logout Success",
            "data": None,
        }

    @router.get("/@me", description="프로필 조회")
    async def get_profile(
        self,
        current_user: "ODMUser" = Depends(get_current_user),
    ):
        return {
            "message": "Profile found",
            "data": {
                "username": current_user.username,
                "email": current_user.email,
                "profile_url": current_user.profile_url,
            },
        }

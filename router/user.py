import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi_restful.cbv import cbv
from passlib.context import CryptContext

from entity.user import User as ODMUser
from aiogoogle import Aiogoogle, auth as aiogoogle_auth
import aiogoogle
from service.credential import depends_credential, Credential, get_current_user

load_dotenv(verbose=True)
router = APIRouter(prefix="/user", tags=["user"])

GOOGLE_CLIENT_CREDS = aiogoogle_auth.creds.ClientCreds(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scopes=["profile", "email"],
    redirect_uri="http://localhost:8000/user/authorization_url",
)
GOOGLE_STATE = uuid.uuid4().hex


@cbv(router)
class User:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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

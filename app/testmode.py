import os
import logging
from dotenv import load_dotenv
from utils.log import Logger
from entity.user import User as ODMUser

logger = Logger.create(__name__, level=logging.DEBUG)
load_dotenv()

if os.getenv("TEST_MODE") == "true":
    logger.info("Test Mode On")
    TEST_USER_ACCESS_TOKEN = (
        "eySPARKTESTAAAAAA" + os.urandom(6).hex() + "BK00000000007218"
    )
    SPARK_TEST_USER_PROFILE = (
        "https://lh3.googleusercontent.com/a"
        "/ACg8ocKJXng59DxsYIIwhbuRCDTQjh0YBseiGNxu1urEuPJmBtBUk3hc=s96-c"
    )
    logger.debug(f"Test User Access Token: " + TEST_USER_ACCESS_TOKEN)


async def get_or_create_test_user() -> "ODMUser":
    odm_user = await ODMUser.find(
        {"email": "SPARK.TESTUSER@internal.temp"}
    ).first_or_none()
    if not odm_user:
        odm_user = ODMUser(
            name="Spark Kim",
            username="testuser.internal",
            email="SPARK.TESTUSER@internal.temp",
            profile_url=SPARK_TEST_USER_PROFILE,
        )
        odm_user = await odm_user.create()
    return odm_user

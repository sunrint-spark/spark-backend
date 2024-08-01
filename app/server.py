import os
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from fastapi import FastAPI
from router import home, user, gpt
from utils.log import Logger

logger = Logger.create(__name__, level=logging.DEBUG)
load_dotenv()


@asynccontextmanager
async def lifespan(_server: FastAPI):
    motor_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(
        database=motor_client[os.getenv("MONGODB_DATABASE")],
        document_models=[
            "entity.test.Test",
            "entity.user.User",
        ],
    )
    logger.info("Connected to MongoDB")
    yield


app = FastAPI(
    title="Spark",
    description="Spark API",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(home.router)
app.include_router(user.router)
app.include_router(gpt.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

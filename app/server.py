import os
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import user, realtime, flow, brainstorm

from utils.log import Logger

logger = Logger.create(__name__, level=logging.DEBUG)
load_dotenv()


@asynccontextmanager
async def lifespan(_server: FastAPI):
    motor_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(
        database=motor_client[os.getenv("MONGODB_DATABASE")],
        document_models=[
            "entity.user.User",
            "entity.flow.Flow",
        ],
    )
    logger.info("Connected to MongoDB")
    _server.state.motor_client = motor_client  # MongoDB 클라이언트를 상태에 저장
    yield
    motor_client.close()
    logger.info("Disconnected from MongoDB")


app = FastAPI(
    title="Spark",
    description="Spark API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(realtime.router)
app.include_router(flow.router)
app.include_router(brainstorm.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

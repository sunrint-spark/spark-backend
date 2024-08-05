from fastapi import APIRouter, Depends, HTTPException, status ,Request
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from entity.models import Flow

router = APIRouter(
    prefix="/flows",
    tags=["Flows"],
)

async def get_motor_client(request:Request):

    return request.app.state.motor_client

@router.post("/", response_model=Flow, status_code=status.HTTP_201_CREATED)
async def create_flow(flow: Flow):
    try:
        print(flow)
        await flow.create()
        return flow
    except Exception as e:
        # 예외 처리 및 로깅
        logger.error(f"Error creating flow: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.put("/{flow_id}", response_model=Flow)
async def update_flow(flow_id: PydanticObjectId, flow: Flow, motor_client: AsyncIOMotorClient = Depends(get_motor_client)):
    db_flow = await Flow.get(flow_id)
    if db_flow is None:
        raise HTTPException(status_code=404, detail="Flow not found")

    flow_update_data = flow.dict(exclude_unset=True, exclude={"is_community"})
    for key, value in flow_update_data.items():
        setattr(db_flow, key, value)

    db_flow.is_community = flow.is_community

    await db_flow.save()
    return db_flow
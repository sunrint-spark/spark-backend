from beanie import Document
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Dict, Literal


class EditorOption(BaseModel):
    viewport: Dict[str, int]


class FlowUserPermission(BaseModel):
    permission: list[Literal["read", "write"]]


class Flow(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    editor_option: Dict[str, EditorOption] = Field(default={})
    nodes: List[dict] = Field(default=[])
    edges: List[dict] = Field(default=[])
    permission: Dict[str, List[FlowUserPermission]] = Field(default=[])

    class Settings:
        name = "flows"  # MongoDB 컬렉션 이름

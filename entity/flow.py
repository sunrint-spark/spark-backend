from beanie import Document
from pydantic import BaseModel, Field, field_serializer
from uuid import UUID, uuid4
from typing import List, Dict, Literal


class Node(BaseModel):
    id: str
    type: str
    position: Dict[str, int]
    measured: Dict[str, int] | dict
    data: dict
    selected: bool
    dragging: bool


class Edge(BaseModel):
    id: str
    source: str
    target: str


class EditorOption(BaseModel):
    viewport: Dict[str, int]


class Flow(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    editor_option: Dict[str, EditorOption] = Field(default={})
    nodes: List[Node] = Field(default=[])
    edges: List[Edge] = Field(default=[])
    permission: Dict[str, list[Literal["read", "write", "owner"]]] = Field(default=[])

    @field_serializer('id')
    def serialize_id(self, id: UUID):
        return str(id)

    class Settings:
        name = "flows"  # MongoDB 컬렉션 이름

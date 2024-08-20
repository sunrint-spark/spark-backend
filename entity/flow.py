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


class Flow(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    editor_option: Dict[str, EditorOption] = Field(default={})
    nodes: List[Node] = Field(default=[])
    edges: List[Edge] = Field(default=[])

    @field_serializer("id")
    def serialize_id(self, id: UUID):
        return str(id)

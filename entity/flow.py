from beanie import Document
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Literal, NewType

UserId = NewType("UserId", str)


class NodeData(BaseModel):
    content: Optional[str] = None
    generated: bool = False
    prompt_address: Optional[str] = None
    label: Optional[str] = None
    ai_generated: Optional[bool] = None
    request: Optional[Dict] = None


class Node(BaseModel):
    id: str
    node_type: str
    position: Dict[str, int]
    data: NodeData


class Edge(BaseModel):
    id: str
    edge_type: str
    source: str
    target: str


class EditorOption(BaseModel):
    viewport: Dict[str, int]


class FlowUserPermission(BaseModel):
    permission: list[Literal["read", "write"]]


class Flow(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    editor_option: Dict[UserId, EditorOption] = Field(default={})
    nodes: List[Node] = Field(default=[])
    edges: List[Edge] = Field(default=[])
    permission: Dict[UserId, List[FlowUserPermission]] = Field(default=[])

    class Settings:
        name = "flows"  # MongoDB 컬렉션 이름

from beanie import Document
from pydantic import BaseModel
from typing import List, Optional, Dict


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


class Flow(Document):
    editor_option: EditorOption
    nodes: List[Node]
    edges: List[Edge]
    is_community: bool = False

    class Settings:
        name = "flows"  # MongoDB 컬렉션 이름

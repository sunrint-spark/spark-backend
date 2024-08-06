from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class NodeData(BaseModel):
    inputContent: Optional[str] = None
    generated: bool = False
    promptAddress: Optional[str] = None
    label: Optional[str] = None
    aiGenerated: Optional[bool] = None
    request: Optional[Dict] = None

class Node(BaseModel):
    id: str
    type: str
    position: Dict[str, int]
    data: NodeData

class Edge(BaseModel):
    id: str
    type: str
    source: str
    target: str

class EditorOption(BaseModel):
    viewport: Dict[str, int]

class Flow(Document):
    editorOption: EditorOption
    nodes: List[Node]
    edges: List[Edge]
    is_community: bool = False


    class Settings:
        name = "flows"  # MongoDB 컬렉션 이름

from typing import Any

from pydantic import BaseModel


class FrontendModal(BaseModel):
    type: str
    title: str
    message: str


class FrontendAction(BaseModel):
    modals: list[FrontendModal]
    action: list[dict[str, Any]]

from pydantic import BaseModel
from beanie import Document


class Test(Document):
    name: str
    age: int
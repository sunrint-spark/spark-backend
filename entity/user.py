from uuid import UUID, uuid4
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class User(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    username: str = Indexed(str, max_length=100)
    email: EmailStr = Indexed(EmailStr)
    profile_url: str | None = Field(max_length=100)

    class Settings:
        name = "users"

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {UUID: str}

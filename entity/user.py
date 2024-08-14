from uuid import UUID, uuid4
from beanie import Document, Indexed
from pydantic import ConfigDict, Field, field_serializer


class User(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    name: str = Indexed(str, max_length=50)
    username: str = Indexed(str, max_length=100)
    email: str = Indexed(str)
    profile_url: str | None = Field(max_length=100)
    approved: bool = Field(default=False)
    recent: list[dict[str, str]] = Field(default=[])

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={UUID: str},
    )

    @field_serializer('id')
    def serialize_id(self, id: UUID):
        return str(id)

    class Settings:
        name = "users"

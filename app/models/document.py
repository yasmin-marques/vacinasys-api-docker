from datetime import datetime, timezone

from beanie import Document as BeanieDocument
from pydantic import Field


def utc_now():
    return datetime.now(timezone.utc)


class Document(BeanieDocument):
    original_filename: str = Field(max_length=255)
    content_type: str = Field(max_length=120)
    extension: str = Field(max_length=20)
    size_bytes: int = Field(ge=0)

    created_at: datetime = Field(default_factory=utc_now)

    campanha_id: str
    # quando migrar Campanha, decidir se vale a pena trocar para PydanticObjectId ou usar Link

    class Settings:
        name = "documents"
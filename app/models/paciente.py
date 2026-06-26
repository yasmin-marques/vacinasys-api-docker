from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Paciente(Document):
    usuario_id: PydanticObjectId

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "pacientes"
        indexes = [
            "usuario_id",
        ]
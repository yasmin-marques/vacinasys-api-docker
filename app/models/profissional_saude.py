from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProfissionalSaude(Document):
    usuario_id: PydanticObjectId
    grau_formacao: str = Field(max_length=120)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "profissionais_saude"
        indexes = [
            "usuario_id",
            "grau_formacao",
        ]
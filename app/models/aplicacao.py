from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import Field


class Aplicacao(Document):
    id_aplicacao: int | None = None

    data: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    id_paciente: PydanticObjectId
    id_profissional: PydanticObjectId
    id_admin: PydanticObjectId
    id_lote: int
    local: str = Field(max_length=120)

    class Settings:
        name = "aplicacoes"
        indexes = [
            "id_aplicacao",
            "data",
            "id_paciente",
            "id_profissional",
            "id_admin",
            "id_lote",
            "local",
        ]
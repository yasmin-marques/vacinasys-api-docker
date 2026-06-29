from datetime import date

from beanie import Document, PydanticObjectId
from pydantic import Field


class CampanhaVacina(Document):
    id_campanha: int
    codigo_vacina: str = Field(max_length=30)

    class Settings:
        name = "campanhas_vacinas"
        indexes = [
            "id_campanha",
            "codigo_vacina",
        ]


class Campanha(Document):
    id_campanha: int | None = None

    data_inicio: date
    data_fim: date | None = None
    nome_campanha: str = Field(max_length=120)

    id_admin: PydanticObjectId

    class Settings:
        name = "campanhas"
        indexes = [
            "id_campanha",
            "nome_campanha",
            "data_inicio",
            "data_fim",
            "id_admin",
        ]
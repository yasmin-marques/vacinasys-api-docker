from datetime import date

from beanie import Document
from pydantic import Field


class Lote(Document):
    id_lote: int | None = None

    validade: date
    data_chegada: date
    quantidade: int = Field(ge=0)
    cnpj_fornecedor: str = Field(max_length=18)

    codigo_vacina: str = Field(max_length=30)

    class Settings:
        name = "lotes"
        indexes = [
            "id_lote",
            "validade",
            "data_chegada",
            "codigo_vacina",
        ]
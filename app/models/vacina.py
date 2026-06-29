from beanie import Document
from pydantic import Field


class Vacina(Document):
    codigo_vacina: str = Field(max_length=30)

    nome: str = Field(max_length=120)
    publico_alvo: str = Field(max_length=120)
    doenca: str = Field(max_length=120)
    quantidade_doses: int = Field(ge=1)
    cnpj_fabricante: str = Field(max_length=18)

    class Settings:
        name = "vacinas"
        indexes = [
            "codigo_vacina",
            "nome",
            "doenca",
        ]
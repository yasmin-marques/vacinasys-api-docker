from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .vacina import Vacina
    from .aplicacao import Aplicacao


class Lote(SQLModel, table=True):
    __tablename__ = "lotes"

    id_lote: int | None = Field(default=None, primary_key=True)

    validade: date
    data_chegada: date
    quantidade: int = Field(ge=0)
    cnpj_fornecedor: str = Field(max_length=18)

    codigo_vacina: str = Field(
        foreign_key="vacinas.codigo_vacina",
        max_length=30
    )

    vacina: "Vacina" = Relationship(back_populates="lotes")
    aplicacoes: list["Aplicacao"] = Relationship(back_populates="lote")

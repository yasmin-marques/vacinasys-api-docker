from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from .campanha import CampanhaVacina
if TYPE_CHECKING:
    from .lote import Lote
    from .campanha import Campanha

class Vacina(SQLModel, table=True):
    __tablename__ = "vacinas"

    codigo_vacina: str = Field(primary_key=True, max_length=30)

    nome: str = Field(index=True, max_length=120)
    publico_alvo: str = Field(max_length=120)
    doenca: str = Field(index=True, max_length=120)
    quantidade_doses: int = Field(ge=1)
    cnpj_fabricante: str = Field(max_length=18)

    lotes: list["Lote"] = Relationship(back_populates="vacina")

    campanhas: list["Campanha"] = Relationship(
        back_populates="vacinas",
        link_model=CampanhaVacina,
    )
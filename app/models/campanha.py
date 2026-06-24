from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .administrador import Administrador
    from .vacina import Vacina
    from .document import Document

class CampanhaVacina(SQLModel, table=True):
    __tablename__ = "campanhas_vacinas"

    id_campanha: int = Field(
        foreign_key="campanhas.id_campanha",
        primary_key=True
    )

    codigo_vacina: str = Field(
        foreign_key="vacinas.codigo_vacina",
        primary_key=True,
        max_length=30
    )

class Campanha(SQLModel, table=True):
    __tablename__ = "campanhas"

    id_campanha: int | None = Field(default=None, primary_key=True)

    data_inicio: date
    data_fim: date | None = None
    nome_campanha: str = Field(index=True, max_length=120)

    id_admin: int = Field(foreign_key="administradores.id_admin")

    admin: "Administrador" = Relationship(back_populates="campanhas")

    vacinas: list["Vacina"] = Relationship(
        back_populates="campanhas",
        link_model=CampanhaVacina,
    )

    documents: list["Document"] = Relationship(back_populates="campanha")



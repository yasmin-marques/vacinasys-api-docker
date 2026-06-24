from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .usuario import Usuario
    from .aplicacao import Aplicacao

class Paciente(SQLModel, table=True):
    __tablename__ = "pacientes"

    id_paciente: int = Field(foreign_key="usuarios.id_usuario", primary_key=True)

    usuario: "Usuario" = Relationship(back_populates="paciente")

    aplicacoes: list["Aplicacao"] = Relationship(back_populates="paciente")
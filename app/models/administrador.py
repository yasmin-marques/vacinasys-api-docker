from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .usuario import Usuario
    from .campanha import Campanha
    from .aplicacao import Aplicacao

class Administrador(SQLModel, table=True):
    __tablename__ = "administradores"

    id_admin: int = Field(foreign_key="usuarios.id_usuario", primary_key=True,)

    usuario: "Usuario" = Relationship(back_populates="administrador")

    campanhas: list["Campanha"] = Relationship(back_populates="admin")
    aplicacoes: list["Aplicacao"] = Relationship(back_populates="admin")
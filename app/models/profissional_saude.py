from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .usuario import Usuario
    from .aplicacao import Aplicacao

class ProfissionalSaude(SQLModel, table=True):
    __tablename__ = "profissionais_saude"

    id_profissional: int = Field(foreign_key="usuarios.id_usuario", primary_key=True)
    grau_formacao: str = Field(max_length=120)

    usuario: "Usuario" = Relationship(back_populates="profissional")

    aplicacoes: list["Aplicacao"] = Relationship(back_populates="profissional")
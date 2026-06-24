from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paciente import Paciente
    from .profissional_saude import ProfissionalSaude
    from .administrador import Administrador


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id_usuario: int | None = Field(default=None, primary_key=True)

    pnome: str = Field(max_length=80)
    unome: str = Field(max_length=80)
    senha: str = Field(max_length=255)
    telefone: str = Field(max_length=20)

    email: str = Field(index=True, max_length=120, sa_column_kwargs={"unique": True})
    cpf_usuario: str = Field(max_length=14, sa_column_kwargs={"unique": True})

    paciente: "Paciente" = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"uselist": False},
    )

    profissional: "ProfissionalSaude" = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"uselist": False},
    )

    administrador: "Administrador" = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"uselist": False},
    )
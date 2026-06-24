from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .paciente import Paciente
    from .profissional_saude import ProfissionalSaude
    from .administrador import Administrador
    from .lote import Lote

class Aplicacao(SQLModel, table=True):
    __tablename__ = "aplicacoes"

    id_aplicacao: int | None = Field(default=None, primary_key=True)

    data: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    id_paciente: int = Field(foreign_key="pacientes.id_paciente")
    id_profissional: int = Field(foreign_key="profissionais_saude.id_profissional")
    id_admin: int = Field(foreign_key="administradores.id_admin")
    id_lote: int = Field(foreign_key="lotes.id_lote")
    local: str = Field(max_length=120)

    paciente: "Paciente" = Relationship(back_populates="aplicacoes")
    profissional: "ProfissionalSaude" = Relationship(back_populates="aplicacoes")
    admin: "Administrador" = Relationship(back_populates="aplicacoes")
    lote: "Lote" = Relationship(back_populates="aplicacoes")



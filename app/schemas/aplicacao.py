from datetime import datetime

from sqlmodel import SQLModel, Field

from .administrador import AdministradorReadDetalhado
from .lote import LoteReadComVacina
from .paciente import PacienteReadDetalhado
from .profissional_saude import ProfissionalSaudeReadDetalhado


class AplicacaoCreate(SQLModel):
    data: datetime | None = None
    id_paciente: int
    id_profissional: int
    id_admin: int
    id_lote: int
    local: str = Field(max_length=120)


class AplicacaoUpdate(SQLModel):
    data: datetime | None = None
    id_paciente: int | None = None
    id_profissional: int | None = None
    id_admin: int | None = None
    id_lote: int | None = None
    local: str | None = Field(default=None, max_length=120)


class AplicacaoRead(SQLModel):
    id_aplicacao: int
    data: datetime
    id_paciente: int
    id_profissional: int
    id_admin: int
    id_lote: int
    local: str


class AplicacaoReadDetalhada(AplicacaoRead):
    paciente: PacienteReadDetalhado | None = None
    profissional: ProfissionalSaudeReadDetalhado | None = None
    admin: AdministradorReadDetalhado | None = None
    lote: LoteReadComVacina | None = None
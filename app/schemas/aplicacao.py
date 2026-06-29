from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.administrador import AdministradorReadDetalhado
from app.schemas.lote import LoteReadComVacina
from app.schemas.paciente import PacienteReadDetalhado
from app.schemas.profissional_saude import ProfissionalSaudeReadDetalhado


class AplicacaoCreate(BaseModel):
    data: datetime | None = None
    id_paciente: PydanticObjectId
    id_profissional: PydanticObjectId
    id_admin: PydanticObjectId
    id_lote: int
    local: str = Field(max_length=120)

    model_config = ConfigDict(str_strip_whitespace=True)


class AplicacaoUpdate(BaseModel):
    data: datetime | None = None
    id_paciente: PydanticObjectId | None = None
    id_profissional: PydanticObjectId | None = None
    id_admin: PydanticObjectId | None = None
    id_lote: int | None = None
    local: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(str_strip_whitespace=True)


class AplicacaoRead(BaseModel):
    id_aplicacao: int
    data: datetime
    id_paciente: PydanticObjectId
    id_profissional: PydanticObjectId
    id_admin: PydanticObjectId
    id_lote: int
    local: str

    model_config = ConfigDict(from_attributes=True)


class AplicacaoReadDetalhada(AplicacaoRead):
    paciente: PacienteReadDetalhado | None = None
    profissional: ProfissionalSaudeReadDetalhado | None = None
    admin: AdministradorReadDetalhado | None = None
    lote: LoteReadComVacina | None = None
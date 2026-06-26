from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.usuario import UsuarioResumo


class ProfissionalSaudeBase(BaseModel):
    grau_formacao: str = Field(max_length=120)

    model_config = ConfigDict(str_strip_whitespace=True)


class ProfissionalSaudeCreate(ProfissionalSaudeBase):
    usuario_id: PydanticObjectId


class ProfissionalSaudeUpdate(BaseModel):
    grau_formacao: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(str_strip_whitespace=True)


class ProfissionalSaudeRead(ProfissionalSaudeBase):
    id: PydanticObjectId
    usuario_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfissionalSaudeReadDetalhado(ProfissionalSaudeRead):
    usuario: UsuarioResumo | None = None
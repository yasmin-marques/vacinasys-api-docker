from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.schemas.usuario import UsuarioResumo


class PacienteCreate(BaseModel):
    usuario_id: PydanticObjectId


class PacienteUpdate(BaseModel):
    pass


class PacienteRead(BaseModel):
    id: PydanticObjectId
    usuario_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PacienteReadDetalhado(PacienteRead):
    usuario: UsuarioResumo | None = None
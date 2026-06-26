from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.schemas.usuario import UsuarioResumo


class AdministradorCreate(BaseModel):
    usuario_id: PydanticObjectId


class AdministradorUpdate(BaseModel):
    pass


class AdministradorRead(BaseModel):
    id: PydanticObjectId
    usuario_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdministradorReadDetalhado(AdministradorRead):
    usuario: UsuarioResumo | None = None
from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    pnome: str = Field(min_length=1, max_length=80)
    unome: str = Field(min_length=1, max_length=80)
    email: EmailStr = Field(max_length=120)
    telefone: str = Field(max_length=20)
    cpf_usuario: str = Field(min_length=11, max_length=14)

    model_config = ConfigDict(str_strip_whitespace=True)


class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=6, max_length=255)


class UsuarioUpdate(BaseModel):
    pnome: str | None = Field(default=None, min_length=1, max_length=80)
    unome: str | None = Field(default=None, min_length=1, max_length=80)
    email: EmailStr | None = Field(default=None, max_length=120)
    senha: str | None = Field(default=None, min_length=6, max_length=255)
    telefone: str | None = Field(default=None, max_length=20)
    cpf_usuario: str | None = Field(default=None, min_length=11, max_length=14)

    model_config = ConfigDict(str_strip_whitespace=True)


class UsuarioRead(UsuarioBase):
    id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioResumo(BaseModel):
    id: PydanticObjectId
    pnome: str
    unome: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
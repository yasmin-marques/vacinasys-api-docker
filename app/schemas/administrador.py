from sqlmodel import SQLModel

from .usuario import UsuarioResumo


class AdministradorCreate(SQLModel):
    id_admin: int


class AdministradorUpdate(SQLModel):
    pass


class AdministradorRead(SQLModel):
    id_admin: int


class AdministradorReadDetalhado(AdministradorRead):
    usuario: UsuarioResumo | None = None
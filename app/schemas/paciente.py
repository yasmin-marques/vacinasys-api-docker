from sqlmodel import SQLModel

from .usuario import UsuarioResumo


class PacienteCreate(SQLModel):
    id_paciente: int


class PacienteUpdate(SQLModel):
    pass


class PacienteRead(SQLModel):
    id_paciente: int


class PacienteReadDetalhado(PacienteRead):
    usuario: UsuarioResumo | None = None
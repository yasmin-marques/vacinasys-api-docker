from sqlmodel import SQLModel, Field


class UsuarioBase(SQLModel):
    pnome: str = Field(max_length=80)
    unome: str = Field(max_length=80)
    email: str = Field(max_length=120)
    telefone: str = Field(max_length=20)
    cpf_usuario: str = Field(max_length=14)


class UsuarioCreate(UsuarioBase):
    senha: str = Field(max_length=255)


class UsuarioUpdate(SQLModel):
    pnome: str | None = Field(default=None, max_length=80)
    unome: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=120)
    senha: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=20)
    cpf_usuario: str | None = Field(default=None, max_length=14)


class UsuarioRead(UsuarioBase):
    id_usuario: int


class UsuarioResumo(SQLModel):
    id_usuario: int
    pnome: str
    unome: str
    email: str
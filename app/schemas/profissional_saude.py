from sqlmodel import SQLModel, Field

from .usuario import UsuarioResumo


class ProfissionalSaudeBase(SQLModel):
    grau_formacao: str = Field(max_length=120)


class ProfissionalSaudeCreate(ProfissionalSaudeBase):
    id_profissional: int


class ProfissionalSaudeUpdate(SQLModel):
    grau_formacao: str | None = Field(default=None, max_length=120)


class ProfissionalSaudeRead(ProfissionalSaudeBase):
    id_profissional: int


class ProfissionalSaudeReadDetalhado(ProfissionalSaudeRead):
    usuario: UsuarioResumo | None = None
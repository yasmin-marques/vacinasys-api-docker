from datetime import date

from sqlmodel import SQLModel, Field

from .administrador import AdministradorReadDetalhado
from .vacina import VacinaResumo


class CampanhaBase(SQLModel):
    nome_campanha: str = Field(max_length=120)
    data_inicio: date
    data_fim: date | None = None
    id_admin: int


class CampanhaCreate(CampanhaBase):
    pass


class CampanhaUpdate(SQLModel):
    nome_campanha: str | None = Field(default=None, max_length=120)
    data_inicio: date | None = None
    data_fim: date | None = None
    id_admin: int | None = None


class CampanhaRead(CampanhaBase):
    id_campanha: int


class CampanhaResumo(SQLModel):
    id_campanha: int
    nome_campanha: str
    data_inicio: date
    data_fim: date | None = None


class CampanhaReadDetalhada(CampanhaRead):
    admin: AdministradorReadDetalhado | None = None
    vacinas: list[VacinaResumo] = Field(default_factory=list)


class CampanhaVacinaCreate(SQLModel):
    id_campanha: int
    codigo_vacina: str = Field(max_length=30)


class CampanhaVacinaRead(CampanhaVacinaCreate):
    pass
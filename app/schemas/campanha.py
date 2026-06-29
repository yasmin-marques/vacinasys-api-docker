from datetime import date

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.administrador import AdministradorReadDetalhado
from app.schemas.vacina import VacinaResumo


class CampanhaBase(BaseModel):
    nome_campanha: str = Field(max_length=120)
    data_inicio: date
    data_fim: date | None = None
    id_admin: PydanticObjectId

    model_config = ConfigDict(str_strip_whitespace=True)


class CampanhaCreate(CampanhaBase):
    pass


class CampanhaUpdate(BaseModel):
    nome_campanha: str | None = Field(default=None, max_length=120)
    data_inicio: date | None = None
    data_fim: date | None = None
    id_admin: PydanticObjectId | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class CampanhaRead(CampanhaBase):
    id_campanha: int

    model_config = ConfigDict(from_attributes=True)


class CampanhaResumo(BaseModel):
    id_campanha: int
    nome_campanha: str
    data_inicio: date
    data_fim: date | None = None

    model_config = ConfigDict(from_attributes=True)


class CampanhaReadDetalhada(CampanhaRead):
    admin: AdministradorReadDetalhado | None = None
    vacinas: list[VacinaResumo] = Field(default_factory=list)


class CampanhaVacinaCreate(BaseModel):
    codigo_vacina: str = Field(max_length=30)

    model_config = ConfigDict(str_strip_whitespace=True)


class CampanhaVacinaRead(BaseModel):
    id_campanha: int
    codigo_vacina: str

    model_config = ConfigDict(from_attributes=True)
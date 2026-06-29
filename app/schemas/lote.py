from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.vacina import VacinaResumo


class LoteBase(BaseModel):
    validade: date
    data_chegada: date
    quantidade: int = Field(ge=0)
    cnpj_fornecedor: str = Field(max_length=18)
    codigo_vacina: str = Field(max_length=30)

    model_config = ConfigDict(str_strip_whitespace=True)


class LoteCreate(LoteBase):
    pass


class LoteUpdate(BaseModel):
    validade: date | None = None
    data_chegada: date | None = None
    quantidade: int | None = Field(default=None, ge=0)
    cnpj_fornecedor: str | None = Field(default=None, max_length=18)
    codigo_vacina: str | None = Field(default=None, max_length=30)

    model_config = ConfigDict(str_strip_whitespace=True)


class LoteRead(LoteBase):
    id_lote: int

    model_config = ConfigDict(from_attributes=True)


class LoteReadComVacina(LoteRead):
    vacina: VacinaResumo | None = None
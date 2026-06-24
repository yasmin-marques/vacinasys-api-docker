from datetime import date

from sqlmodel import SQLModel, Field

from .vacina import VacinaResumo


class LoteBase(SQLModel):
    validade: date
    data_chegada: date
    quantidade: int = Field(ge=0)
    cnpj_fornecedor: str = Field(max_length=18)
    codigo_vacina: str = Field(max_length=30)


class LoteCreate(LoteBase):
    pass


class LoteUpdate(SQLModel):
    validade: date | None = None
    data_chegada: date | None = None
    quantidade: int | None = Field(default=None, ge=0)
    cnpj_fornecedor: str | None = Field(default=None, max_length=18)
    codigo_vacina: str | None = Field(default=None, max_length=30)


class LoteRead(LoteBase):
    id_lote: int


class LoteReadComVacina(LoteRead):
    vacina: VacinaResumo | None = None
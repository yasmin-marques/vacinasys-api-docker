from sqlmodel import SQLModel, Field


class VacinaBase(SQLModel):
    codigo_vacina: str = Field(max_length=30)
    nome: str = Field(max_length=120)
    doenca: str = Field(max_length=120)
    quantidade_doses: int = Field(ge=1)
    publico_alvo: str = Field(max_length=120)
    cnpj_fabricante: str = Field(max_length=18)


class VacinaCreate(VacinaBase):
    pass


class VacinaUpdate(SQLModel):
    nome: str | None = Field(default=None, max_length=120)
    doenca: str | None = Field(default=None, max_length=120)
    quantidade_doses: int | None = Field(default=None, ge=1)
    publico_alvo: str | None = Field(default=None, max_length=120)
    cnpj_fabricante: str | None = Field(default=None, max_length=18)


class VacinaRead(VacinaBase):
    pass


class VacinaResumo(SQLModel):
    codigo_vacina: str
    nome: str
    doenca: str
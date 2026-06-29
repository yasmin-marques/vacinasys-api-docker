from pydantic import BaseModel, ConfigDict, Field


class VacinaBase(BaseModel):
    codigo_vacina: str = Field(max_length=30)
    nome: str = Field(max_length=120)
    doenca: str = Field(max_length=120)
    quantidade_doses: int = Field(ge=1)
    publico_alvo: str = Field(max_length=120)
    cnpj_fabricante: str = Field(max_length=18)

    model_config = ConfigDict(str_strip_whitespace=True)


class VacinaCreate(VacinaBase):
    pass


class VacinaUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=120)
    doenca: str | None = Field(default=None, max_length=120)
    quantidade_doses: int | None = Field(default=None, ge=1)
    publico_alvo: str | None = Field(default=None, max_length=120)
    cnpj_fabricante: str | None = Field(default=None, max_length=18)

    model_config = ConfigDict(str_strip_whitespace=True)


class VacinaRead(VacinaBase):
    pass


class VacinaResumo(BaseModel):
    codigo_vacina: str
    nome: str
    doenca: str

    model_config = ConfigDict(from_attributes=True)
from datetime import datetime

from sqlmodel import SQLModel, Field

from .campanha import CampanhaResumo


class DocumentBase(SQLModel):
    original_filename: str = Field(max_length=255)
    content_type: str = Field(max_length=120)
    extension: str = Field(max_length=20)
    size_bytes: int = Field(ge=0)
    id_campanha: int


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(SQLModel):
    original_filename: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=120)
    extension: str | None = Field(default=None, max_length=20)
    size_bytes: int | None = Field(default=None, ge=0)
    id_campanha: int | None = None


class DocumentRead(DocumentBase):
    id: int
    created_at: datetime


class DocumentReadDetalhado(DocumentRead):
    campanha: CampanhaResumo | None = None
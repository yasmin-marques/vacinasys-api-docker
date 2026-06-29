from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    """Campos de metadados comuns a um documento."""

    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    created_at: datetime


class DocumentRead(DocumentBase):
    """Representação de leitura dos metadados de um documento."""

    id: PydanticObjectId
    campanha_id: str

    model_config = ConfigDict(from_attributes=True)


# Mantido por compatibilidade com importações antigas.
DocumentResponse = DocumentRead
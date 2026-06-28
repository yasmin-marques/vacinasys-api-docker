from datetime import datetime

from pydantic import BaseModel


class DocumentBase(BaseModel):
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    created_at: datetime


class DocumentResponse(DocumentBase):
    id: str
    campanha_id: str
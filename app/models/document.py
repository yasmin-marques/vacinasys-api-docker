from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .campanha import Campanha


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)

    original_filename: str = Field(max_length=255)
    content_type: str = Field(max_length=120)
    extension: str = Field(max_length=20)
    size_bytes: int = Field(ge=0)

    created_at: datetime = Field(default_factory=utc_now_naive)

    id_campanha: int = Field(foreign_key="campanhas.id_campanha")

    campanha: "Campanha" = Relationship(back_populates="documents")
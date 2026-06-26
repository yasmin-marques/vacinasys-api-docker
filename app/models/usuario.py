from datetime import datetime, timezone

from beanie import Document
from pydantic import EmailStr, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Document):
    pnome: str = Field(min_length=1, max_length=80)
    unome: str = Field(min_length=1, max_length=80)
    email: EmailStr = Field(max_length=120)
    senha: str = Field(min_length=6, max_length=255)
    telefone: str = Field(max_length=20)
    cpf_usuario: str = Field(min_length=11, max_length=14)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "usuarios"
        indexes = [
            "email",
            "cpf_usuario",
            "pnome",
            "unome",
        ]
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.models.administrador import Administrador
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.usuario import Usuario
from app.models.document import Document

client: AsyncMongoClient | None = None


async def init_database() -> None:
    global client

    client = AsyncMongoClient(settings.mongodb_url)
    database = client[settings.mongodb_database]

    print(type(client))
    print(type(database))

    await init_beanie(
        database=database,
        document_models=[
            Usuario,
            Paciente,
            ProfissionalSaude,
            Administrador,
            Document
        ],
    )


async def close_database() -> None:
    if client is not None:
        await client.close()
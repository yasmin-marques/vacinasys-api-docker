from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.administrador import Administrador
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.usuario import Usuario

client: AsyncIOMotorClient | None = None


async def init_database() -> None:
    global client

    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.mongodb_database]

    await init_beanie(
        database=database,
        document_models=[
            Usuario,
            Paciente,
            ProfissionalSaude,
            Administrador,
        ],
    )


async def close_database() -> None:
    if client is not None:
        client.close()
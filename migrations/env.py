import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))


from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.administrador import Administrador
from app.models.profissional_saude import ProfissionalSaude
from app.models.vacina import Vacina
from app.models.lote import Lote
from app.models.campanha import Campanha, CampanhaVacina
from app.models.aplicacao import Aplicacao
from app.models.document import Document


load_dotenv()


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


DATABASE_URL = os.getenv("DATABASE_URL") 

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi definida no arquivo .env")


config.set_main_option("sqlalchemy.url", DATABASE_URL)


target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
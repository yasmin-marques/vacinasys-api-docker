from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from app.config import settings
from app.database import close_database, init_database
from app.routes import administradores, pacientes, profissionais, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield
    await close_database()


app = FastAPI(
    title=settings.app_name,
    description="API Web para gerenciamento de sistema de vacinação.",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "erro": "Dados inválidos.",
            "detalhes": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "erro": "Erro interno inesperado.",
        },
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VacinaSys API funcionando.",
        "database": "MongoDB",
        "odm": "Beanie",
    }


app.include_router(usuarios.router)
app.include_router(pacientes.router)
app.include_router(profissionais.router)
app.include_router(administradores.router)

add_pagination(app)
# app/main.py
"""Ponto de entrada da aplicação VacinaSys."""

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.routes import (
    administradores,
    aplicacoes,
    campanhas,
    lotes,
    pacientes,
    profissionais,
    usuarios,
    vacinas,
    document
)

app = FastAPI(
    title="VacinaSys",
    description="API Web para gerenciamento de sistema de vacinação.",
    version="0.1.0",
)

# Registro das rotas
app.include_router(usuarios.router)
app.include_router(pacientes.router)
app.include_router(profissionais.router)
app.include_router(administradores.router)
app.include_router(vacinas.router)
app.include_router(lotes.router)
app.include_router(campanhas.router)
app.include_router(aplicacoes.router)
app.include_router(document.router)   

@app.get("/", tags=["Root"])
async def root():
    """Health check da API."""
    return {"message": "VacinaSys API funcionando."}


add_pagination(app)

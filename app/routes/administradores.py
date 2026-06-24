
"""Rotas para gerenciamento de Administradores."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.administrador import Administrador
from app.models.usuario import Usuario
from app.schemas.administrador import (
    AdministradorCreate,
    AdministradorRead,
    AdministradorReadDetalhado,
    AdministradorUpdate,
)

router = APIRouter(prefix="/administradores", tags=["Administradores"])


def _query_detalhada():
    """Query base com joinedload"""
    return select(Administrador).options(
        joinedload(Administrador.usuario)  
    )


@router.post("/", response_model=AdministradorRead, status_code=status.HTTP_201_CREATED)
async def criar_administrador(
    dados: AdministradorCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria um novo administrador (vinculado a um usuário existente)."""
    usuario = await session.get(Usuario, dados.id_admin)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.id_admin} não encontrado.",
        )
    existente = await session.get(Administrador, dados.id_admin)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Administrador com id {dados.id_admin} já existe.",
        )
    admin = Administrador.model_validate(dados)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@router.get("/", response_model=Page[AdministradorReadDetalhado])
async def listar_administradores(
    order_by: str = Query(
        "id_admin",
        enum=["id_admin"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todos os administradores com dados do usuário e ordenação escolhida pelo cliente."""
    coluna = Administrador.id_admin
    query = _query_detalhada().order_by(
        coluna.desc() if order == "desc" else coluna.asc()
    )
    return await paginate(session, query)

@router.get("/{id_admin}", response_model=AdministradorReadDetalhado)
async def obter_administrador(
    id_admin: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém um administrador pelo ID com dados do usuário."""
    resultado = await session.exec(
        _query_detalhada().where(Administrador.id_admin == id_admin)
    )
    admin = resultado.first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )
    return admin


@router.patch("/{id_admin}", response_model=AdministradorRead)
async def atualizar_administrador(
    id_admin: int,
    dados: AdministradorUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza um administrador."""
    admin = await session.get(Administrador, id_admin)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(admin, campo, valor)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@router.delete("/{id_admin}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_administrador(
    id_admin: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um administrador."""
    admin = await session.get(Administrador, id_admin)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )
    await session.delete(admin)
    await session.commit()


"""Rotas para gerenciamento de Usuários."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    dados: UsuarioCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria um novo usuário."""
    resultado = await session.exec(
        select(Usuario).where(
            (Usuario.email == dados.email) | (Usuario.cpf_usuario == dados.cpf_usuario)
        )
    )
    if resultado.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este e-mail ou CPF.",
        )
    usuario = Usuario.model_validate(dados)
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


@router.get("/", response_model=Page[UsuarioRead])
async def listar_usuarios(
    session: AsyncSession = Depends(get_session),
):
    """Lista todos os usuários com paginação."""
    query = select(Usuario).order_by(Usuario.pnome, Usuario.unome)
    return await paginate(session, query)


@router.get("/busca", response_model=Page[UsuarioRead])
async def buscar_usuarios_por_nome(
    nome: str = Query(..., description="Texto parcial para busca no nome"),
    session: AsyncSession = Depends(get_session),
):
    """(c) Busca usuários por texto parcial no nome."""
    query = (
        select(Usuario)
        .where(
            Usuario.pnome.ilike(f"%{nome}%") | Usuario.unome.ilike(f"%{nome}%")
        )
        .order_by(Usuario.pnome)
    )
    return await paginate(session, query)


@router.get("/{id_usuario}", response_model=UsuarioRead)
async def obter_usuario(
    id_usuario: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém um usuário pelo ID."""
    usuario = await session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )
    return usuario


@router.patch("/{id_usuario}", response_model=UsuarioRead)
async def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente um usuário."""
    usuario = await session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(usuario, campo, valor)
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(
    id_usuario: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um usuário."""
    usuario = await session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )
    await session.delete(usuario)
    await session.commit()

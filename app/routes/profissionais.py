
"""Rotas para gerenciamento de Profissionais de Saúde."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.profissional_saude import ProfissionalSaude
from app.models.usuario import Usuario
from app.schemas.profissional_saude import (
    ProfissionalSaudeCreate,
    ProfissionalSaudeRead,
    ProfissionalSaudeReadDetalhado,
    ProfissionalSaudeUpdate,
)

router = APIRouter(prefix="/profissionais", tags=["Profissionais de Saúde"])


def _query_detalhada():
    """Query base com joinedload"""
    return select(ProfissionalSaude).options(
        joinedload(ProfissionalSaude.usuario)
    )


@router.post("/", response_model=ProfissionalSaudeRead, status_code=status.HTTP_201_CREATED)
async def criar_profissional(
    dados: ProfissionalSaudeCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria um novo profissional de saúde (vinculado a um usuário existente)."""
    usuario = await session.get(Usuario, dados.id_profissional)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.id_profissional} não encontrado.",
        )
    existente = await session.get(ProfissionalSaude, dados.id_profissional)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profissional com id {dados.id_profissional} já existe.",
        )
    profissional = ProfissionalSaude.model_validate(dados)
    session.add(profissional)
    await session.commit()
    await session.refresh(profissional)
    return profissional

@router.get("/", response_model=Page[ProfissionalSaudeReadDetalhado])
async def listar_profissionais(
    order_by: str = Query(
        "id_profissional",
        enum=["id_profissional", "grau_formacao"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todos os profissionais com dados do usuário e ordenação escolhida pelo cliente."""
    colunas = {
        "id_profissional": ProfissionalSaude.id_profissional,
        "grau_formacao": ProfissionalSaude.grau_formacao,
    }
    coluna = colunas.get(order_by, ProfissionalSaude.id_profissional)
    query = _query_detalhada().order_by(
        coluna.desc() if order == "desc" else coluna.asc()
    )
    return await paginate(session, query)

@router.get("/por-formacao", response_model=Page[ProfissionalSaudeReadDetalhado])
async def listar_por_formacao(
    formacao: str = Query(..., description="Texto parcial do grau de formação"),
    order_by: str = Query("id_profissional", enum=["id_profissional", "grau_formacao"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/c/f) Lista profissionais filtrando por grau de formação, com ordenação."""
    colunas = {
        "id_profissional": ProfissionalSaude.id_profissional,
        "grau_formacao": ProfissionalSaude.grau_formacao,
    }
    coluna = colunas.get(order_by, ProfissionalSaude.id_profissional)
    query = (
        _query_detalhada()
        .where(ProfissionalSaude.grau_formacao.ilike(f"%{formacao}%"))
        .order_by(coluna.desc() if order == "desc" else coluna.asc())
    )
    return await paginate(session, query)

@router.get("/{id_profissional}", response_model=ProfissionalSaudeReadDetalhado)
async def obter_profissional(
    id_profissional: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém um profissional pelo ID com dados do usuário."""
    resultado = await session.exec(
        _query_detalhada().where(ProfissionalSaude.id_profissional == id_profissional)
    )
    profissional = resultado.first()
    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )
    return profissional


@router.patch("/{id_profissional}", response_model=ProfissionalSaudeRead)
async def atualizar_profissional(
    id_profissional: int,
    dados: ProfissionalSaudeUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente um profissional de saúde."""
    profissional = await session.get(ProfissionalSaude, id_profissional)
    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(profissional, campo, valor)
    session.add(profissional)
    await session.commit()
    await session.refresh(profissional)
    return profissional


@router.delete("/{id_profissional}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_profissional(
    id_profissional: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um profissional de saúde."""
    profissional = await session.get(ProfissionalSaude, id_profissional)
    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )
    await session.delete(profissional)
    await session.commit()

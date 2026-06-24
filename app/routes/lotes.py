
"""Rotas para gerenciamento de Lotes de Vacinas."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import extract, func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.lote import Lote
from app.models.vacina import Vacina
from app.schemas.lote import LoteCreate, LoteRead, LoteReadComVacina, LoteUpdate

router = APIRouter(prefix="/lotes", tags=["Lotes"])

_COLUNAS_ORDENACAO = {
    "id_lote": Lote.id_lote,
    "validade": Lote.validade,
    "data_chegada": Lote.data_chegada,
    "quantidade": Lote.quantidade,
}


def _query_com_vacina():
    return select(Lote).options(selectinload(Lote.vacina))


def _aplicar_ordenacao(query, order_by: str, order: str):
    coluna = _COLUNAS_ORDENACAO.get(order_by, Lote.id_lote)
    return query.order_by(coluna.desc() if order == "desc" else coluna.asc())


@router.post("/", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
async def criar_lote(
    dados: LoteCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria um novo lote de vacina."""
    vacina = await session.get(Vacina, dados.codigo_vacina)
    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{dados.codigo_vacina}' não encontrada.",
        )
    lote = Lote.model_validate(dados)
    session.add(lote)
    await session.commit()
    await session.refresh(lote)
    return lote

@router.get("/", response_model=Page[LoteReadComVacina])
async def listar_lotes(
    order_by: str = Query(
        "id_lote",
        enum=["id_lote", "validade", "data_chegada", "quantidade"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todos os lotes com dados da vacina e ordenação escolhida pelo cliente."""
    query = _aplicar_ordenacao(_query_com_vacina(), order_by, order)
    return await paginate(session, query)

@router.get("/por-vacina", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_vacina(
    codigo_vacina: str = Query(..., description="Código da vacina"),
    order_by: str = Query("validade", enum=["id_lote", "validade", "data_chegada", "quantidade"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista lotes filtrados por vacina, com ordenação."""
    query = _query_com_vacina().where(Lote.codigo_vacina == codigo_vacina)
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/validade", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_validade(
    data_inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    order_by: str = Query("validade", enum=["id_lote", "validade", "data_chegada", "quantidade"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista lotes com validade dentro de um intervalo de datas, com ordenação."""
    query = _query_com_vacina().where(
        Lote.validade >= data_inicio,
        Lote.validade <= data_fim,
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/validade-por-ano", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_ano_validade(
    ano: int = Query(..., description="Ano de validade do lote (ex: 2025)"),
    order_by: str = Query("validade", enum=["id_lote", "validade", "data_chegada", "quantidade"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista lotes que vencem em determinado ano, com ordenação."""
    query = _query_com_vacina().where(extract("year", Lote.validade) == ano)
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/estoque-por-vacina", response_model=list[dict])
async def estoque_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por quantidade total"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f/g) Soma a quantidade disponível de cada vacina cruzando Lote → Vacina."""
    total_col = func.sum(Lote.quantidade).label("quantidade_total")
    stmt = (
        select(Vacina.codigo_vacina, Vacina.nome, total_col)
        .join(Lote, Lote.codigo_vacina == Vacina.codigo_vacina)
        .group_by(Vacina.codigo_vacina, Vacina.nome)
        .order_by(total_col.desc() if order == "desc" else total_col.asc())
    )
    resultado = await session.exec(stmt)
    return [
        {"codigo_vacina": row[0], "nome_vacina": row[1], "quantidade_total": row[2]}
        for row in resultado.all()
    ]

@router.get("/contagem-por-vacina", response_model=list[dict])
async def contagem_lotes_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por total de lotes"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f/g) Conta o número de lotes cadastrados por vacina."""
    total_col = func.count(Lote.id_lote).label("total_lotes")
    stmt = (
        select(Vacina.codigo_vacina, Vacina.nome, total_col)
        .join(Lote, Lote.codigo_vacina == Vacina.codigo_vacina)
        .group_by(Vacina.codigo_vacina, Vacina.nome)
        .order_by(total_col.desc() if order == "desc" else total_col.asc())
    )
    resultado = await session.exec(stmt)
    return [
        {"codigo_vacina": row[0], "nome_vacina": row[1], "total_lotes": row[2]}
        for row in resultado.all()
    ]

@router.get("/{id_lote}", response_model=LoteReadComVacina)
async def obter_lote(
    id_lote: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém um lote pelo ID com dados da vacina."""
    resultado = await session.exec(
        _query_com_vacina().where(Lote.id_lote == id_lote)
    )
    lote = resultado.first()
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )
    return lote


@router.patch("/{id_lote}", response_model=LoteRead)
async def atualizar_lote(
    id_lote: int,
    dados: LoteUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente um lote."""
    lote = await session.get(Lote, id_lote)
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )
    if dados.codigo_vacina:
        vacina = await session.get(Vacina, dados.codigo_vacina)
        if not vacina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacina '{dados.codigo_vacina}' não encontrada.",
            )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(lote, campo, valor)
    session.add(lote)
    await session.commit()
    await session.refresh(lote)
    return lote


@router.delete("/{id_lote}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_lote(
    id_lote: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um lote."""
    lote = await session.get(Lote, id_lote)
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )
    await session.delete(lote)
    await session.commit()

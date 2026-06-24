
"""Rotas para gerenciamento de Aplicações de Vacinas."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import extract, func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.aplicacao import Aplicacao
from app.models.administrador import Administrador
from app.models.lote import Lote
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.vacina import Vacina
from app.schemas.aplicacao import (
    AplicacaoCreate,
    AplicacaoRead,
    AplicacaoReadDetalhada,
    AplicacaoUpdate,
)

router = APIRouter(prefix="/aplicacoes", tags=["Aplicações"])

_COLUNAS_ORDENACAO = {
    "data": Aplicacao.data,
    "id_aplicacao": Aplicacao.id_aplicacao,
    "local": Aplicacao.local,
    "id_paciente": Aplicacao.id_paciente,
    "id_profissional": Aplicacao.id_profissional,
}


def _query_detalhada():
    """Query base com eager loading de todos os relacionamentos."""
    return select(Aplicacao).options(
        selectinload(Aplicacao.paciente).selectinload(Paciente.usuario),
        selectinload(Aplicacao.profissional).selectinload(ProfissionalSaude.usuario),
        selectinload(Aplicacao.admin).selectinload(Administrador.usuario),
        selectinload(Aplicacao.lote).selectinload(Lote.vacina),
    )


def _aplicar_ordenacao(query, order_by: str, order: str):
    """Aplica ordenação dinâmica à query."""
    coluna = _COLUNAS_ORDENACAO.get(order_by, Aplicacao.data)
    return query.order_by(coluna.desc() if order == "desc" else coluna.asc())


@router.post("/", response_model=AplicacaoRead, status_code=status.HTTP_201_CREATED)
async def criar_aplicacao(
    dados: AplicacaoCreate,
    session: AsyncSession = Depends(get_session),
):
    """Registra uma nova aplicação de vacina."""
    for model, fk, label in [
        (Paciente, dados.id_paciente, "Paciente"),
        (ProfissionalSaude, dados.id_profissional, "Profissional"),
        (Administrador, dados.id_admin, "Administrador"),
        (Lote, dados.id_lote, "Lote"),
    ]:
        if not await session.get(model, fk):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{label} {fk} não encontrado.",
            )
    aplicacao = Aplicacao.model_validate(dados)
    session.add(aplicacao)
    await session.commit()
    await session.refresh(aplicacao)
    return aplicacao

@router.get("/", response_model=Page[AplicacaoReadDetalhada])
async def listar_aplicacoes(
    order_by: str = Query(
        "data",
        enum=["data", "id_aplicacao", "local", "id_paciente", "id_profissional"],
        description="Campo de ordenação",
    ),
    order: str = Query("desc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todas as aplicações com dados completos e ordenação escolhida pelo cliente."""
    query = _aplicar_ordenacao(_query_detalhada(), order_by, order)
    return await paginate(session, query)

@router.get("/por-paciente/{id_paciente}", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_paciente(
    id_paciente: int,
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista aplicações de um paciente específico, com ordenação."""
    query = _query_detalhada().where(Aplicacao.id_paciente == id_paciente)
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-profissional/{id_profissional}", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_profissional(
    id_profissional: int,
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista aplicações realizadas por um profissional específico, com ordenação."""
    query = _query_detalhada().where(Aplicacao.id_profissional == id_profissional)
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-data", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_data(
    data_inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista aplicações dentro de um intervalo de datas, com ordenação."""
    query = _query_detalhada().where(
        func.date(Aplicacao.data) >= data_inicio,
        func.date(Aplicacao.data) <= data_fim,
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-ano", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_ano(
    ano: int = Query(..., description="Ano da aplicação (ex: 2024)"),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista aplicações de um determinado ano, com ordenação."""
    query = _query_detalhada().where(
        extract("year", Aplicacao.data) == ano
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-local", response_model=Page[AplicacaoReadDetalhada])
async def buscar_por_local(
    local: str = Query(..., description="Texto parcial do local de aplicação"),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(c/f) Busca aplicações por texto parcial no local, com ordenação."""
    query = _query_detalhada().where(Aplicacao.local.ilike(f"%{local}%"))
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/total", response_model=dict)
async def contar_aplicacoes(
    session: AsyncSession = Depends(get_session),
):
    """(e) Retorna a quantidade total de aplicações registradas."""
    resultado = await session.exec(select(func.count(Aplicacao.id_aplicacao)))
    total = resultado.one()
    return {"total_aplicacoes": total}


@router.get("/contagem-por-lote", response_model=list[dict])
async def contagem_por_lote(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por total"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f) Conta o número de aplicações por lote, com ordenação."""
    total_col = func.count(Aplicacao.id_aplicacao).label("total")
    stmt = (
        select(Aplicacao.id_lote, total_col)
        .group_by(Aplicacao.id_lote)
        .order_by(total_col.desc() if order == "desc" else total_col.asc())
    )
    resultado = await session.exec(stmt)
    return [{"id_lote": row[0], "total_aplicacoes": row[1]} for row in resultado.all()]

@router.get("/contagem-por-vacina", response_model=list[dict])
async def contagem_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por total"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f/g) Conta aplicações agrupadas por vacina, cruzando Aplicacao → Lote → Vacina."""
    total_col = func.count(Aplicacao.id_aplicacao).label("total")
    stmt = (
        select(Vacina.codigo_vacina, Vacina.nome, total_col)
        .join(Lote, Lote.codigo_vacina == Vacina.codigo_vacina)
        .join(Aplicacao, Aplicacao.id_lote == Lote.id_lote)
        .group_by(Vacina.codigo_vacina, Vacina.nome)
        .order_by(total_col.desc() if order == "desc" else total_col.asc())
    )
    resultado = await session.exec(stmt)
    return [
        {"codigo_vacina": row[0], "nome_vacina": row[1], "total_aplicacoes": row[2]}
        for row in resultado.all()
    ]

@router.get("/contagem-por-profissional", response_model=list[dict])
async def contagem_por_profissional(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por total"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f/g) Conta aplicações por profissional de saúde, cruzando Aplicacao → ProfissionalSaude → Usuario."""
    from app.models.usuario import Usuario
    total_col = func.count(Aplicacao.id_aplicacao).label("total")
    stmt = (
        select(
            ProfissionalSaude.id_profissional,
            Usuario.pnome,
            Usuario.unome,
            total_col,
        )
        .join(ProfissionalSaude, Aplicacao.id_profissional == ProfissionalSaude.id_profissional)
        .join(Usuario, ProfissionalSaude.id_profissional == Usuario.id_usuario)
        .group_by(ProfissionalSaude.id_profissional, Usuario.pnome, Usuario.unome)
        .order_by(total_col.desc() if order == "desc" else total_col.asc())
    )
    resultado = await session.exec(stmt)
    return [
        {
            "id_profissional": row[0],
            "nome": f"{row[1]} {row[2]}",
            "total_aplicacoes": row[3],
        }
        for row in resultado.all()
    ]


@router.get("/{id_aplicacao}", response_model=AplicacaoReadDetalhada)
async def obter_aplicacao(
    id_aplicacao: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém uma aplicação pelo ID com todos os dados relacionados."""
    resultado = await session.exec(
        _query_detalhada().where(Aplicacao.id_aplicacao == id_aplicacao)
    )
    aplicacao = resultado.first()
    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )
    return aplicacao


@router.patch("/{id_aplicacao}", response_model=AplicacaoRead)
async def atualizar_aplicacao(
    id_aplicacao: int,
    dados: AplicacaoUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente uma aplicação."""
    aplicacao = await session.get(Aplicacao, id_aplicacao)
    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )
    fk_checks = [
        (Paciente, dados.id_paciente, "Paciente"),
        (ProfissionalSaude, dados.id_profissional, "Profissional"),
        (Administrador, dados.id_admin, "Administrador"),
        (Lote, dados.id_lote, "Lote"),
    ]
    for model, fk, label in fk_checks:
        if fk is not None and not await session.get(model, fk):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{label} {fk} não encontrado.",
            )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(aplicacao, campo, valor)
    session.add(aplicacao)
    await session.commit()
    await session.refresh(aplicacao)
    return aplicacao


@router.delete("/{id_aplicacao}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_aplicacao(
    id_aplicacao: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove uma aplicação."""
    aplicacao = await session.get(Aplicacao, id_aplicacao)
    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )
    await session.delete(aplicacao)
    await session.commit()


"""Rotas para gerenciamento de Vacinas."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.vacina import Vacina
from app.schemas.vacina import VacinaCreate, VacinaRead, VacinaUpdate

router = APIRouter(prefix="/vacinas", tags=["Vacinas"])

_COLUNAS_ORDENACAO = {
    "nome": Vacina.nome,
    "codigo_vacina": Vacina.codigo_vacina,
    "doenca": Vacina.doenca,
    "quantidade_doses": Vacina.quantidade_doses,
    "publico_alvo": Vacina.publico_alvo,
}


def _aplicar_ordenacao(query, order_by: str, order: str):
    coluna = _COLUNAS_ORDENACAO.get(order_by, Vacina.nome)
    return query.order_by(coluna.desc() if order == "desc" else coluna.asc())


@router.post("/", response_model=VacinaRead, status_code=status.HTTP_201_CREATED)
async def criar_vacina(
    dados: VacinaCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria uma nova vacina."""
    existente = await session.get(Vacina, dados.codigo_vacina)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vacina com código '{dados.codigo_vacina}' já existe.",
        )
    vacina = Vacina.model_validate(dados)
    session.add(vacina)
    await session.commit()
    await session.refresh(vacina)
    return vacina

@router.get("/", response_model=Page[VacinaRead])
async def listar_vacinas(
    order_by: str = Query(
        "nome",
        enum=["nome", "codigo_vacina", "doenca", "quantidade_doses", "publico_alvo"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todas as vacinas com ordenação escolhida pelo cliente."""
    query = _aplicar_ordenacao(select(Vacina), order_by, order)
    return await paginate(session, query)

@router.get("/busca", response_model=Page[VacinaRead])
async def buscar_vacinas_por_nome(
    nome: str = Query(..., description="Texto parcial para busca no nome da vacina"),
    order_by: str = Query("nome", enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(c/f) Busca vacinas por texto parcial no nome, com ordenação."""
    query = select(Vacina).where(Vacina.nome.ilike(f"%{nome}%"))
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-doenca", response_model=Page[VacinaRead])
async def listar_vacinas_por_doenca(
    doenca: str = Query(..., description="Nome da doença (parcial)"),
    order_by: str = Query("nome", enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista vacinas filtradas por doença, com ordenação."""
    query = select(Vacina).where(Vacina.doenca.ilike(f"%{doenca}%"))
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-publico-alvo", response_model=Page[VacinaRead])
async def listar_vacinas_por_publico_alvo(
    publico: str = Query(..., description="Texto parcial do público-alvo (ex: criança, idoso)"),
    order_by: str = Query("nome", enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista vacinas filtradas por público-alvo, com ordenação."""
    query = select(Vacina).where(Vacina.publico_alvo.ilike(f"%{publico}%"))
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/total", response_model=dict)
async def contar_vacinas(
    session: AsyncSession = Depends(get_session),
):
    """(e) Retorna a quantidade total de vacinas cadastradas."""
    resultado = await session.exec(select(func.count(Vacina.codigo_vacina)))
    total = resultado.one()
    return {"total_vacinas": total}

@router.get("/contagem-por-doses", response_model=list[dict])
async def contagem_vacinas_por_doses(
    order: str = Query("asc", enum=["asc", "desc"], description="Ordenação pelo número de doses"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f) Agrupa vacinas pelo número de doses necessárias."""
    total_col = func.count(Vacina.codigo_vacina).label("total_vacinas")
    stmt = (
        select(Vacina.quantidade_doses, total_col)
        .group_by(Vacina.quantidade_doses)
        .order_by(
            Vacina.quantidade_doses.desc() if order == "desc" else Vacina.quantidade_doses.asc()
        )
    )
    resultado = await session.exec(stmt)
    return [
        {"quantidade_doses": row[0], "total_vacinas": row[1]}
        for row in resultado.all()
    ]

@router.get("/{codigo_vacina}", response_model=VacinaRead)
async def obter_vacina(
    codigo_vacina: str,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém uma vacina pelo seu código."""
    vacina = await session.get(Vacina, codigo_vacina)
    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{codigo_vacina}' não encontrada.",
        )
    return vacina


@router.patch("/{codigo_vacina}", response_model=VacinaRead)
async def atualizar_vacina(
    codigo_vacina: str,
    dados: VacinaUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente uma vacina."""
    vacina = await session.get(Vacina, codigo_vacina)
    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{codigo_vacina}' não encontrada.",
        )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(vacina, campo, valor)
    session.add(vacina)
    await session.commit()
    await session.refresh(vacina)
    return vacina


@router.delete("/{codigo_vacina}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_vacina(
    codigo_vacina: str,
    session: AsyncSession = Depends(get_session),
):
    """Remove uma vacina."""
    vacina = await session.get(Vacina, codigo_vacina)
    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{codigo_vacina}' não encontrada.",
        )
    await session.delete(vacina)
    await session.commit()

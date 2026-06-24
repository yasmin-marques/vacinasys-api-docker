
"""Rotas para gerenciamento de Campanhas de Vacinação."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import extract, func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.campanha import Campanha, CampanhaVacina
from app.models.administrador import Administrador
from app.models.vacina import Vacina
from app.schemas.campanha import (
    CampanhaCreate,
    CampanhaRead,
    CampanhaReadDetalhada,
    CampanhaUpdate,
    CampanhaVacinaCreate,
    CampanhaVacinaRead,
)

router = APIRouter(prefix="/campanhas", tags=["Campanhas"])

_COLUNAS_ORDENACAO = {
    "data_inicio": Campanha.data_inicio,
    "data_fim": Campanha.data_fim,
    "nome_campanha": Campanha.nome_campanha,
    "id_campanha": Campanha.id_campanha,
}

def _query_detalhada():
    """Query base com eager loading de admin e vacinas."""
    return select(Campanha).options(
        selectinload(Campanha.admin).selectinload(Administrador.usuario),
        selectinload(Campanha.vacinas),
    )


def _aplicar_ordenacao(query, order_by: str, order: str):
    """Aplica ordenação dinâmica à query."""
    coluna = _COLUNAS_ORDENACAO.get(order_by, Campanha.data_inicio)
    return query.order_by(coluna.desc() if order == "desc" else coluna.asc())


@router.post("/", response_model=CampanhaRead, status_code=status.HTTP_201_CREATED)
async def criar_campanha(
    dados: CampanhaCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria uma nova campanha de vacinação."""
    admin = await session.get(Administrador, dados.id_admin)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {dados.id_admin} não encontrado.",
        )
    campanha = Campanha.model_validate(dados)
    session.add(campanha)
    await session.commit()
    await session.refresh(campanha)
    return campanha

@router.get("/", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas(
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "data_fim", "nome_campanha", "id_campanha"],
        description="Campo de ordenação",
    ),
    order: str = Query("desc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista campanhas com ordenação escolhida pelo cliente."""
    query = _aplicar_ordenacao(_query_detalhada(), order_by, order)
    return await paginate(session, query)

@router.get("/busca", response_model=Page[CampanhaReadDetalhada])
async def buscar_campanhas_por_nome(
    nome: str = Query(..., description="Texto parcial do nome da campanha"),
    order_by: str = Query("data_inicio", enum=["data_inicio", "nome_campanha", "id_campanha"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(c/f) Busca campanhas por texto parcial no nome, com ordenação."""
    query = _query_detalhada().where(Campanha.nome_campanha.ilike(f"%{nome}%"))
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-ano", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_ano(
    ano: int = Query(..., description="Ano de início da campanha (ex: 2024)"),
    order_by: str = Query("data_inicio", enum=["data_inicio", "nome_campanha", "id_campanha"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista campanhas que iniciaram em determinado ano. Compatível com PostgreSQL e SQLite."""
    query = _query_detalhada().where(
        extract("year", Campanha.data_inicio) == ano
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/por-periodo", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_periodo(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    order_by: str = Query("data_inicio", enum=["data_inicio", "nome_campanha", "id_campanha"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(d/f) Lista campanhas que iniciam dentro de um intervalo de datas."""
    query = _query_detalhada().where(
        Campanha.data_inicio >= data_inicio,
        Campanha.data_inicio <= data_fim,
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)

@router.get("/total", response_model=dict)
async def contar_campanhas(
    session: AsyncSession = Depends(get_session),
):
    """(e) Retorna a quantidade total de campanhas cadastradas."""
    resultado = await session.exec(select(func.count(Campanha.id_campanha)))
    total = resultado.one()
    return {"total_campanhas": total}


@router.get("/contagem-por-ano", response_model=list[dict])
async def contagem_campanhas_por_ano(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por ano"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f) Conta o número de campanhas agrupadas por ano de início."""
    ano_col = extract("year", Campanha.data_inicio).label("ano")
    stmt = (
        select(ano_col, func.count(Campanha.id_campanha).label("total"))
        .group_by(ano_col)
        .order_by(ano_col.desc() if order == "desc" else ano_col.asc())
    )
    resultado = await session.exec(stmt)
    return [{"ano": int(row[0]), "total_campanhas": row[1]} for row in resultado.all()]


@router.get("/contagem-vacinas-por-campanha", response_model=list[dict])
async def contagem_vacinas_por_campanha(
    order: str = Query("desc", enum=["asc", "desc"], description="Ordenação por total"),
    session: AsyncSession = Depends(get_session),
):
    """(e/f) Conta o número de vacinas associadas a cada campanha."""
    stmt = (
        select(
            Campanha.id_campanha,
            Campanha.nome_campanha,
            func.count(CampanhaVacina.codigo_vacina).label("total_vacinas"),
        )
        .join(CampanhaVacina, CampanhaVacina.id_campanha == Campanha.id_campanha, isouter=True)
        .group_by(Campanha.id_campanha, Campanha.nome_campanha)
        .order_by(
            func.count(CampanhaVacina.codigo_vacina).desc()
            if order == "desc"
            else func.count(CampanhaVacina.codigo_vacina).asc()
        )
    )
    resultado = await session.exec(stmt)
    return [
        {"id_campanha": row[0], "nome_campanha": row[1], "total_vacinas": row[2]}
        for row in resultado.all()
    ]

@router.get("/por-vacina/{codigo_vacina}", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_vacina(
    codigo_vacina: str,
    order_by: str = Query("data_inicio", enum=["data_inicio", "nome_campanha", "id_campanha"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """(b/f) Lista campanhas que incluem uma vacina específica, com ordenação."""
    query = (
        _query_detalhada()
        .join(CampanhaVacina, CampanhaVacina.id_campanha == Campanha.id_campanha)
        .where(CampanhaVacina.codigo_vacina == codigo_vacina)
    )
    query = _aplicar_ordenacao(query, order_by, order)
    return await paginate(session, query)


# (a) Busca por ID
@router.get("/{id_campanha}", response_model=CampanhaReadDetalhada)
async def obter_campanha(
    id_campanha: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém uma campanha pelo ID com admin e vacinas."""
    resultado = await session.exec(
        _query_detalhada().where(Campanha.id_campanha == id_campanha)
    )
    campanha = resultado.first()
    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )
    return campanha


@router.patch("/{id_campanha}", response_model=CampanhaRead)
async def atualizar_campanha(
    id_campanha: int,
    dados: CampanhaUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza parcialmente uma campanha."""
    campanha = await session.get(Campanha, id_campanha)
    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )
    if dados.id_admin is not None:
        admin = await session.get(Administrador, dados.id_admin)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Administrador {dados.id_admin} não encontrado.",
            )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(campanha, campo, valor)
    session.add(campanha)
    await session.commit()
    await session.refresh(campanha)
    return campanha


@router.delete("/{id_campanha}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_campanha(
    id_campanha: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove uma campanha."""
    campanha = await session.get(Campanha, id_campanha)
    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )
    await session.delete(campanha)
    await session.commit()


# many-to-many

@router.post("/{id_campanha}/vacinas", response_model=CampanhaVacinaRead, status_code=status.HTTP_201_CREATED)
async def adicionar_vacina_campanha(
    id_campanha: int,
    dados: CampanhaVacinaCreate,
    session: AsyncSession = Depends(get_session),
):
    """Associa uma vacina a uma campanha (many-to-many)."""
    campanha = await session.get(Campanha, id_campanha)
    if not campanha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campanha {id_campanha} não encontrada.")
    vacina = await session.get(Vacina, dados.codigo_vacina)
    if not vacina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vacina '{dados.codigo_vacina}' não encontrada.")
    existente = await session.get(CampanhaVacina, (id_campanha, dados.codigo_vacina))
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vacina já associada a esta campanha.")
    cv = CampanhaVacina(id_campanha=id_campanha, codigo_vacina=dados.codigo_vacina)
    session.add(cv)
    await session.commit()
    return cv


@router.delete("/{id_campanha}/vacinas/{codigo_vacina}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_vacina_campanha(
    id_campanha: int,
    codigo_vacina: str,
    session: AsyncSession = Depends(get_session),
):
    """Remove a associação entre uma vacina e uma campanha."""
    cv = await session.get(CampanhaVacina, (id_campanha, codigo_vacina))
    if not cv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associação não encontrada.")
    await session.delete(cv)
    await session.commit()

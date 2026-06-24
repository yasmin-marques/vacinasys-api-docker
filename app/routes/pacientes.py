
"""Rotas para gerenciamento de Pacientes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.schemas.paciente import PacienteCreate, PacienteRead, PacienteReadDetalhado, PacienteUpdate

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def _query_detalhada():
    """Query base com joinedload"""
    return select(Paciente).options(
        joinedload(Paciente.usuario) 
    )


@router.post("/", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
async def criar_paciente(
    dados: PacienteCreate,
    session: AsyncSession = Depends(get_session),
):
    """Cria um novo paciente (vinculado a um usuário existente)."""
    usuario = await session.get(Usuario, dados.id_paciente)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.id_paciente} não encontrado.",
        )
    existente = await session.get(Paciente, dados.id_paciente)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Paciente com id {dados.id_paciente} já existe.",
        )
    paciente = Paciente.model_validate(dados)
    session.add(paciente)
    await session.commit()
    await session.refresh(paciente)
    return paciente

@router.get("/", response_model=Page[PacienteReadDetalhado])
async def listar_pacientes(
    order_by: str = Query(
        "id_paciente",
        enum=["id_paciente"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """(f) Lista todos os pacientes com dados do usuário e ordenação escolhida pelo cliente."""
    coluna = Paciente.id_paciente
    query = _query_detalhada().order_by(
        coluna.desc() if order == "desc" else coluna.asc()
    )
    return await paginate(session, query)

@router.get("/{id_paciente}", response_model=PacienteReadDetalhado)
async def obter_paciente(
    id_paciente: int,
    session: AsyncSession = Depends(get_session),
):
    """(a) Obtém um paciente pelo ID com dados do usuário."""
    resultado = await session.exec(
        _query_detalhada().where(Paciente.id_paciente == id_paciente)
    )
    paciente = resultado.first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )
    return paciente


@router.patch("/{id_paciente}", response_model=PacienteRead)
async def atualizar_paciente(
    id_paciente: int,
    dados: PacienteUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Atualiza um paciente."""
    paciente = await session.get(Paciente, id_paciente)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )
    update_data = dados.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(paciente, campo, valor)
    session.add(paciente)
    await session.commit()
    await session.refresh(paciente)
    return paciente


@router.delete("/{id_paciente}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_paciente(
    id_paciente: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um paciente."""
    paciente = await session.get(Paciente, id_paciente)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )
    await session.delete(paciente)
    await session.commit()

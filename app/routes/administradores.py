from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.administrador import Administrador
from app.models.usuario import Usuario
from app.schemas.administrador import (
    AdministradorCreate,
    AdministradorRead,
    AdministradorReadDetalhado,
    AdministradorUpdate,
)
from app.schemas.usuario import UsuarioResumo

router = APIRouter(prefix="/administradores", tags=["Administradores"])


def utc_now() -> datetime:
    """
    Obtém a data e hora atual em UTC.

    Args:
        Nenhum parâmetro.

    Returns:
        datetime: Data e hora atual com timezone UTC.
    """
    return datetime.now(timezone.utc)


def validar_object_id(id_recebido: str, nome_entidade: str = "ID") -> PydanticObjectId:
    """
    Valida e converte uma string para PydanticObjectId.

    Args:
        id_recebido (str): ID recebido pela rota.
        nome_entidade (str): Nome da entidade usado na mensagem de erro.

    Returns:
        PydanticObjectId: ID validado e convertido.

    Raises:
        HTTPException: Quando o ID informado não possui formato válido de ObjectId.
    """
    try:
        return PydanticObjectId(id_recebido)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{nome_entidade} inválido.",
        )


async def montar_administrador_detalhado(
    administrador: Administrador,
) -> AdministradorReadDetalhado:
    """
    Monta uma resposta detalhada de administrador com os dados do usuário relacionado.

    Args:
        administrador (Administrador): Documento de administrador recuperado do banco de dados.

    Returns:
        AdministradorReadDetalhado: Dados do administrador junto com o resumo do usuário relacionado.
    """
    usuario = await Usuario.get(administrador.usuario_id)

    usuario_resumo = None

    if usuario:
        usuario_resumo = UsuarioResumo.model_validate(usuario)

    return AdministradorReadDetalhado(
        id=administrador.id,
        usuario_id=administrador.usuario_id,
        nivel_acesso=administrador.nivel_acesso,
        setor=administrador.setor,
        ativo=administrador.ativo,
        created_at=administrador.created_at,
        updated_at=administrador.updated_at,
        usuario=usuario_resumo,
    )


async def paginar_administradores(query, params: Params) -> Page[AdministradorReadDetalhado]:
    """
    Aplica paginação em uma consulta de administradores e monta respostas detalhadas.

    Args:
        query: Consulta Beanie usada para buscar os administradores.
        params (Params): Parâmetros de paginação recebidos pela requisição.

    Returns:
        Page[AdministradorReadDetalhado]: Página contendo administradores detalhados e informações de paginação.
    """
    total = await query.count()

    administradores = (
        await query
        .skip((params.page - 1) * params.size)
        .limit(params.size)
        .to_list()
    )

    itens = []

    for administrador in administradores:
        itens.append(await montar_administrador_detalhado(administrador))

    return create_page(itens, total=total, params=params)


async def verificar_administrador_existente(
    usuario_id: PydanticObjectId | None = None,
    administrador_id_ignorado: PydanticObjectId | None = None,
) -> None:
    """
    Verifica se já existe um administrador vinculado ao usuário informado.

    Args:
        usuario_id (PydanticObjectId | None): ID do usuário vinculado ao administrador.
        administrador_id_ignorado (PydanticObjectId | None): ID do administrador que deve ser ignorado na verificação,
            usado em operações de atualização.

    Returns:
        None.

    Raises:
        HTTPException: Quando já existe um administrador vinculado ao usuário informado.
    """
    if not usuario_id:
        return

    filtro_consulta = {"usuario_id": usuario_id}

    if administrador_id_ignorado:
        filtro_consulta["_id"] = {"$ne": administrador_id_ignorado}

    administrador_existente = await Administrador.find_one(filtro_consulta)

    if administrador_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um administrador vinculado a este usuário.",
        )


@router.post("/", response_model=AdministradorRead, status_code=status.HTTP_201_CREATED)
async def criar_administrador(dados: AdministradorCreate):
    usuario = await Usuario.get(dados.usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.usuario_id} não encontrado.",
        )

    await verificar_administrador_existente(usuario_id=dados.usuario_id)

    admin = Administrador(**dados.model_dump())
    await admin.insert()

    return admin


@router.get("/", response_model=Page[AdministradorReadDetalhado])
async def listar_administradores(
    order_by: str = Query(
        "id_admin",
        enum=["id_admin"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    params: Params = Depends(),
):
    campo_ordenacao = "-_id" if order == "desc" else "_id"

    query = Administrador.find_all().sort(campo_ordenacao)

    return await paginar_administradores(query, params)


@router.get("/{id_admin}", response_model=AdministradorReadDetalhado)
async def obter_administrador(id_admin: str):
    object_id = validar_object_id(id_admin, "ID de administrador")

    admin = await Administrador.get(object_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )

    return await montar_administrador_detalhado(admin)


@router.patch("/{id_admin}", response_model=AdministradorRead)
async def atualizar_administrador(
    id_admin: str,
    dados: AdministradorUpdate,
):
    object_id = validar_object_id(id_admin, "ID de administrador")

    admin = await Administrador.get(object_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(admin, campo, valor)

    admin.updated_at = utc_now()
    await admin.save()

    return admin


@router.delete("/{id_admin}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_administrador(id_admin: str):
    object_id = validar_object_id(id_admin, "ID de administrador")

    admin = await Administrador.get(object_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )

    await admin.delete()
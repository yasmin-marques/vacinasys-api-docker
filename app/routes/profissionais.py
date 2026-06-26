from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.profissional_saude import ProfissionalSaude
from app.models.usuario import Usuario
from app.schemas.profissional_saude import (
    ProfissionalSaudeCreate,
    ProfissionalSaudeRead,
    ProfissionalSaudeReadDetalhado,
    ProfissionalSaudeUpdate,
)
from app.schemas.usuario import UsuarioResumo

router = APIRouter(prefix="/profissionais", tags=["Profissionais de Saúde"])


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


async def montar_profissional_detalhado(
    profissional: ProfissionalSaude,
) -> ProfissionalSaudeReadDetalhado:
    """
    Monta uma resposta detalhada de profissional de saúde com os dados do usuário relacionado.

    Args:
        profissional (ProfissionalSaude): Documento de profissional de saúde recuperado do banco de dados.

    Returns:
        ProfissionalSaudeReadDetalhado: Dados do profissional de saúde junto com o resumo do usuário relacionado.
    """
    usuario = await Usuario.get(profissional.usuario_id)

    usuario_resumo = None

    if usuario:
        usuario_resumo = UsuarioResumo.model_validate(usuario)

    return ProfissionalSaudeReadDetalhado(
        id=profissional.id,
        usuario_id=profissional.usuario_id,
        grau_formacao=profissional.grau_formacao,
        created_at=profissional.created_at,
        updated_at=profissional.updated_at,
        usuario=usuario_resumo,
    )


async def paginar_profissionais(
    query,
    params: Params,
) -> Page[ProfissionalSaudeReadDetalhado]:
    """
    Aplica paginação em uma consulta de profissionais de saúde e monta respostas detalhadas.

    Args:
        query: Consulta Beanie usada para buscar os profissionais de saúde.
        params (Params): Parâmetros de paginação recebidos pela requisição.

    Returns:
        Page[ProfissionalSaudeReadDetalhado]: Página contendo profissionais de saúde detalhados e informações de paginação.
    """
    total = await query.count()

    profissionais = await query.skip(
        (params.page - 1) * params.size
    ).limit(
        params.size
    ).to_list()

    itens = []

    for profissional in profissionais:
        itens.append(await montar_profissional_detalhado(profissional))

    return create_page(itens, total=total, params=params)


async def verificar_profissional_existente(
    usuario_id: PydanticObjectId | None = None,
    profissional_id_ignorado: PydanticObjectId | None = None,
) -> None:
    """
    Verifica se já existe um profissional de saúde vinculado ao usuário informado.

    Args:
        usuario_id (PydanticObjectId | None): ID do usuário vinculado ao profissional de saúde.
        profissional_id_ignorado (PydanticObjectId | None): ID do profissional que deve ser ignorado na verificação,
            usado em operações de atualização.

    Returns:
        None.

    Raises:
        HTTPException: Quando já existe um profissional de saúde vinculado ao usuário informado.
    """
    if not usuario_id:
        return

    filtro_consulta = {"usuario_id": usuario_id}

    if profissional_id_ignorado:
        filtro_consulta["_id"] = {"$ne": profissional_id_ignorado}

    profissional_existente = await ProfissionalSaude.find_one(filtro_consulta)

    if profissional_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um profissional vinculado a este usuário.",
        )


def obter_campo_ordenacao(order_by: str, order: str) -> str:
    """
    Converte o campo de ordenação recebido pela rota para o campo usado no MongoDB.

    Args:
        order_by (str): Nome público do campo usado para ordenação.
        order (str): Direção da ordenação, podendo ser "asc" ou "desc".

    Returns:
        str: Campo de ordenação no formato esperado pelo Beanie.
    """
    campos = {
        "id_profissional": "_id",
        "grau_formacao": "grau_formacao",
    }

    campo = campos.get(order_by, "_id")

    return f"-{campo}" if order == "desc" else campo


@router.post("/", response_model=ProfissionalSaudeRead, status_code=status.HTTP_201_CREATED)
async def criar_profissional(dados: ProfissionalSaudeCreate):
    usuario = await Usuario.get(dados.usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.usuario_id} não encontrado.",
        )

    await verificar_profissional_existente(usuario_id=dados.usuario_id)

    profissional = ProfissionalSaude(**dados.model_dump())
    await profissional.insert()

    return profissional


@router.get("/", response_model=Page[ProfissionalSaudeReadDetalhado])
async def listar_profissionais(
    order_by: str = Query(
        "id_profissional",
        enum=["id_profissional", "grau_formacao"],
        description="Campo de ordenação",
    ),
    order: str = Query(
        "asc",
        enum=["asc", "desc"],
        description="Direção da ordenação",
    ),
    params: Params = Depends(),
):
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = ProfissionalSaude.find_all().sort(campo_ordenacao)

    return await paginar_profissionais(query, params)


@router.get("/por-formacao", response_model=Page[ProfissionalSaudeReadDetalhado])
async def listar_por_formacao(
    formacao: str = Query(..., description="Texto parcial do grau de formação"),
    order_by: str = Query(
        "id_profissional",
        enum=["id_profissional", "grau_formacao"],
        description="Campo de ordenação",
    ),
    order: str = Query(
        "asc",
        enum=["asc", "desc"],
        description="Direção da ordenação",
    ),
    params: Params = Depends(),
):
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = ProfissionalSaude.find(
        {
            "grau_formacao": {
                "$regex": formacao,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_profissionais(query, params)


@router.get("/{id_profissional}", response_model=ProfissionalSaudeReadDetalhado)
async def obter_profissional(id_profissional: str):
    object_id = validar_object_id(id_profissional, "ID de profissional")

    profissional = await ProfissionalSaude.get(object_id)

    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )

    return await montar_profissional_detalhado(profissional)


@router.patch("/{id_profissional}", response_model=ProfissionalSaudeRead)
async def atualizar_profissional(
    id_profissional: str,
    dados: ProfissionalSaudeUpdate,
):
    object_id = validar_object_id(id_profissional, "ID de profissional")

    profissional = await ProfissionalSaude.get(object_id)

    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(profissional, campo, valor)

    profissional.updated_at = utc_now()
    await profissional.save()

    return profissional


@router.delete("/{id_profissional}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_profissional(id_profissional: str):
    object_id = validar_object_id(id_profissional, "ID de profissional")

    profissional = await ProfissionalSaude.get(object_id)

    if not profissional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )

    await profissional.delete()
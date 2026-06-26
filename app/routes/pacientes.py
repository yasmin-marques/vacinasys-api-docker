from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.schemas.paciente import PacienteCreate, PacienteRead, PacienteReadDetalhado, PacienteUpdate
from app.schemas.usuario import UsuarioResumo

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


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


async def montar_paciente_detalhado(paciente: Paciente) -> PacienteReadDetalhado:
    """
    Monta uma resposta detalhada de paciente com os dados do usuário relacionado.

    Args:
        paciente (Paciente): Documento de paciente recuperado do banco de dados.

    Returns:
        PacienteReadDetalhado: Dados do paciente junto com o resumo do usuário relacionado.
    """
    usuario = await Usuario.get(paciente.usuario_id)

    usuario_resumo = None

    if usuario:
        usuario_resumo = UsuarioResumo.model_validate(usuario)

    return PacienteReadDetalhado(
        id=paciente.id,
        usuario_id=paciente.usuario_id,
        data_nascimento=paciente.data_nascimento,
        sexo=paciente.sexo,
        cartao_sus=paciente.cartao_sus,
        endereco=paciente.endereco,
        created_at=paciente.created_at,
        updated_at=paciente.updated_at,
        usuario=usuario_resumo,
    )


async def paginar_pacientes(query, params: Params) -> Page[PacienteReadDetalhado]:
    """
    Aplica paginação em uma consulta de pacientes e monta respostas detalhadas.

    Args:
        query: Consulta Beanie usada para buscar os pacientes.
        params (Params): Parâmetros de paginação recebidos pela requisição.

    Returns:
        Page[PacienteReadDetalhado]: Página contendo pacientes detalhados e informações de paginação.
    """
    total = await query.count()

    pacientes = (
        await query
        .skip((params.page - 1) * params.size)
        .limit(params.size)
        .to_list()
    )

    itens = []

    for paciente in pacientes:
        itens.append(await montar_paciente_detalhado(paciente))

    return create_page(itens, total=total, params=params)


async def verificar_paciente_existente(
    usuario_id: PydanticObjectId | None = None,
    cartao_sus: str | None = None,
    paciente_id_ignorado: PydanticObjectId | None = None,
) -> None:
    """
    Verifica se já existe um paciente vinculado ao mesmo usuário ou ao mesmo cartão SUS.

    Args:
        usuario_id (PydanticObjectId | None): ID do usuário vinculado ao paciente.
        cartao_sus (str | None): Número do cartão SUS que será verificado.
        paciente_id_ignorado (PydanticObjectId | None): ID do paciente que deve ser ignorado na verificação,
            usado em operações de atualização.

    Returns:
        None.

    Raises:
        HTTPException: Quando já existe um paciente com o mesmo usuário ou cartão SUS.
    """
    filtros = []

    if usuario_id:
        filtros.append({"usuario_id": usuario_id})

    if cartao_sus:
        filtros.append({"cartao_sus": cartao_sus})

    if not filtros:
        return

    filtro_consulta = {"$or": filtros}

    if paciente_id_ignorado:
        filtro_consulta["_id"] = {"$ne": paciente_id_ignorado}

    paciente_existente = await Paciente.find_one(filtro_consulta)

    if paciente_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um paciente com este usuário ou cartão SUS.",
        )


@router.post("/", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
async def criar_paciente(dados: PacienteCreate):
    usuario = await Usuario.get(dados.usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {dados.usuario_id} não encontrado.",
        )

    await verificar_paciente_existente(
        usuario_id=dados.usuario_id,
        cartao_sus=dados.cartao_sus,
    )

    paciente = Paciente(**dados.model_dump())
    await paciente.insert()

    return paciente


@router.get("/", response_model=Page[PacienteReadDetalhado])
async def listar_pacientes(
    order_by: str = Query(
        "id_paciente",
        enum=["id_paciente"],
        description="Campo de ordenação",
    ),
    order: str = Query("asc", enum=["asc", "desc"], description="Direção da ordenação"),
    params: Params = Depends(),
):
    campo_ordenacao = "-_id" if order == "desc" else "_id"

    query = Paciente.find_all().sort(campo_ordenacao)

    return await paginar_pacientes(query, params)


@router.get("/{id_paciente}", response_model=PacienteReadDetalhado)
async def obter_paciente(id_paciente: str):
    object_id = validar_object_id(id_paciente, "ID de paciente")

    paciente = await Paciente.get(object_id)

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )

    return await montar_paciente_detalhado(paciente)


@router.patch("/{id_paciente}", response_model=PacienteRead)
async def atualizar_paciente(id_paciente: str, dados: PacienteUpdate):
    object_id = validar_object_id(id_paciente, "ID de paciente")

    paciente = await Paciente.get(object_id)

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )

    update_data = dados.model_dump(exclude_unset=True)

    await verificar_paciente_existente(
        cartao_sus=update_data.get("cartao_sus"),
        paciente_id_ignorado=paciente.id,
    )

    for campo, valor in update_data.items():
        setattr(paciente, campo, valor)

    paciente.updated_at = utc_now()
    await paciente.save()

    return paciente


@router.delete("/{id_paciente}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_paciente(id_paciente: str):
    object_id = validar_object_id(id_paciente, "ID de paciente")

    paciente = await Paciente.get(object_id)

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )

    await paciente.delete()
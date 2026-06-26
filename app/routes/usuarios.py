from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def utc_now() -> datetime:
    """
    Obtém a data e hora atual em UTC.

    Args:
        Nenhum parâmetro.

    Returns:
        datetime: Data e hora atual com timezone UTC.
    """
    return datetime.now(timezone.utc)


def validar_object_id(id_usuario: str) -> PydanticObjectId:
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
        return PydanticObjectId(id_usuario)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido.",
        )


async def verificar_email_ou_cpf_existente(
    email: str | None,
    cpf_usuario: str | None,
    usuario_id_ignorado: PydanticObjectId | None = None,
) -> None:
    """
    Verifica se já existe um usuário cadastrado com o mesmo e-mail ou CPF.

    Args:
        email (str | None): E-mail que será verificado.
        cpf_usuario (str | None): CPF que será verificado.
        usuario_id_ignorado (PydanticObjectId | None): ID do usuário que deve ser ignorado na verificação,
            usado em operações de atualização.

    Returns:
        None.

    Raises:
        HTTPException: Quando já existe um usuário com o mesmo e-mail ou CPF.
    """
    filtros = []

    if email:
        filtros.append({"email": email})

    if cpf_usuario:
        filtros.append({"cpf_usuario": cpf_usuario})

    if not filtros:
        return

    filtro_consulta = {"$or": filtros}

    if usuario_id_ignorado:
        filtro_consulta["_id"] = {"$ne": usuario_id_ignorado}

    usuario_existente = await Usuario.find_one(filtro_consulta)

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este e-mail ou CPF.",
        )


@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def criar_usuario(dados: UsuarioCreate):
    await verificar_email_ou_cpf_existente(dados.email, dados.cpf_usuario)

    usuario = Usuario(**dados.model_dump())
    await usuario.insert()

    return usuario


@router.get("/", response_model=Page[UsuarioRead])
async def listar_usuarios():
    query = Usuario.find_all().sort("pnome", "unome")
    return await paginate(query)


@router.get("/busca", response_model=Page[UsuarioRead])
async def buscar_usuarios_por_nome(
    nome: str = Query(..., description="Texto parcial para busca no nome"),
):
    query = Usuario.find(
        {
            "$or": [
                {"pnome": {"$regex": nome, "$options": "i"}},
                {"unome": {"$regex": nome, "$options": "i"}},
            ]
        }
    ).sort("pnome")

    return await paginate(query)


@router.get("/{id_usuario}", response_model=UsuarioRead)
async def obter_usuario(id_usuario: str):
    object_id = validar_object_id(id_usuario)

    usuario = await Usuario.get(object_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )

    return usuario


@router.patch("/{id_usuario}", response_model=UsuarioRead)
async def atualizar_usuario(id_usuario: str, dados: UsuarioUpdate):
    object_id = validar_object_id(id_usuario)

    usuario = await Usuario.get(object_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )

    update_data = dados.model_dump(exclude_unset=True)

    await verificar_email_ou_cpf_existente(
        update_data.get("email"),
        update_data.get("cpf_usuario"),
        usuario.id,
    )

    for campo, valor in update_data.items():
        setattr(usuario, campo, valor)

    usuario.updated_at = utc_now()
    await usuario.save()

    return usuario


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(id_usuario: str):
    object_id = validar_object_id(id_usuario)

    usuario = await Usuario.get(object_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {id_usuario} não encontrado.",
        )

    await usuario.delete()
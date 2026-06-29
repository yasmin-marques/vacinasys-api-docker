from datetime import date, datetime, time, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.administrador import Administrador
from app.models.aplicacao import Aplicacao
from app.models.lote import Lote
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.vacina import Vacina
from app.schemas.administrador import AdministradorReadDetalhado
from app.schemas.aplicacao import (
    AplicacaoCreate,
    AplicacaoRead,
    AplicacaoReadDetalhada,
    AplicacaoUpdate,
)
from app.schemas.lote import LoteReadComVacina
from app.schemas.paciente import PacienteReadDetalhado
from app.schemas.profissional_saude import ProfissionalSaudeReadDetalhado
from app.schemas.vacina import VacinaResumo

router = APIRouter(prefix="/aplicacoes", tags=["Aplicações"])


def obter_campo_ordenacao(order_by: str, order: str) -> str:
    """Retorna o campo usado para ordenar a listagem de aplicações."""
    campos = {
        "data": "data",
        "id_aplicacao": "id_aplicacao",
        "local": "local",
        "id_paciente": "id_paciente",
        "id_profissional": "id_profissional",
    }

    campo = campos.get(order_by, "data")

    return f"-{campo}" if order == "desc" else campo


async def obter_proximo_id_aplicacao() -> int:
    """Calcula o próximo identificador numérico para uma aplicação."""
    aplicacoes = await Aplicacao.find_all().sort("-id_aplicacao").limit(1).to_list()

    if not aplicacoes or aplicacoes[0].id_aplicacao is None:
        return 1

    return aplicacoes[0].id_aplicacao + 1


async def buscar_paciente(id_paciente: PydanticObjectId):
    """Busca um paciente pelo seu identificador do MongoDB."""
    return await Paciente.get(id_paciente)


async def buscar_profissional(id_profissional: PydanticObjectId):
    """Busca um profissional de saúde pelo seu identificador do MongoDB."""
    return await ProfissionalSaude.get(id_profissional)


async def buscar_administrador(id_admin: PydanticObjectId):
    """Busca um administrador pelo seu identificador do MongoDB."""
    return await Administrador.get(id_admin)


async def buscar_lote(id_lote: int):
    """Busca um lote pelo seu identificador numérico."""
    return await Lote.find_one({"id_lote": id_lote})


async def montar_lote_com_vacina(lote: Lote | None):
    """Monta a resposta de um lote incluindo a vacina associada."""
    if not lote:
        return None

    vacina = await Vacina.find_one({"codigo_vacina": lote.codigo_vacina})

    vacina_resumo = None

    if vacina:
        vacina_resumo = VacinaResumo.model_validate(vacina)

    return LoteReadComVacina(
        id_lote=lote.id_lote,
        validade=lote.validade,
        data_chegada=lote.data_chegada,
        quantidade=lote.quantidade,
        cnpj_fornecedor=lote.cnpj_fornecedor,
        codigo_vacina=lote.codigo_vacina,
        vacina=vacina_resumo,
    )


async def montar_aplicacao_detalhada(aplicacao: Aplicacao) -> AplicacaoReadDetalhada:
    """Monta a resposta detalhada de uma aplicação com paciente, profissional, administrador e lote."""
    paciente = await buscar_paciente(aplicacao.id_paciente)
    profissional = await buscar_profissional(aplicacao.id_profissional)
    admin = await buscar_administrador(aplicacao.id_admin)
    lote = await buscar_lote(aplicacao.id_lote)

    paciente_resumo = None
    profissional_resumo = None
    admin_resumo = None

    if paciente:
        try:
            paciente_resumo = PacienteReadDetalhado.model_validate(paciente)
        except Exception:
            paciente_resumo = None

    if profissional:
        try:
            profissional_resumo = ProfissionalSaudeReadDetalhado.model_validate(profissional)
        except Exception:
            profissional_resumo = None

    if admin:
        try:
            admin_resumo = AdministradorReadDetalhado.model_validate(admin)
        except Exception:
            admin_resumo = None

    lote_resumo = await montar_lote_com_vacina(lote)

    return AplicacaoReadDetalhada(
        id_aplicacao=aplicacao.id_aplicacao,
        data=aplicacao.data,
        id_paciente=aplicacao.id_paciente,
        id_profissional=aplicacao.id_profissional,
        id_admin=aplicacao.id_admin,
        id_lote=aplicacao.id_lote,
        local=aplicacao.local,
        paciente=paciente_resumo,
        profissional=profissional_resumo,
        admin=admin_resumo,
        lote=lote_resumo,
    )


async def paginar_aplicacoes(query, params: Params) -> Page[AplicacaoReadDetalhada]:
    """Aplica paginação manual em uma consulta de aplicações detalhadas."""
    total = await query.count()

    aplicacoes = (
        await query
        .skip((params.page - 1) * params.size)
        .limit(params.size)
        .to_list()
    )

    itens = []

    for aplicacao in aplicacoes:
        itens.append(await montar_aplicacao_detalhada(aplicacao))

    return create_page(itens, total=total, params=params)


async def validar_referencias_aplicacao(
    id_paciente: PydanticObjectId | None = None,
    id_profissional: PydanticObjectId | None = None,
    id_admin: PydanticObjectId | None = None,
    id_lote: int | None = None,
):
    """Valida se paciente, profissional, administrador e lote existem antes da operação."""
    if id_paciente is not None and not await buscar_paciente(id_paciente):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente {id_paciente} não encontrado.",
        )

    if id_profissional is not None and not await buscar_profissional(id_profissional):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profissional {id_profissional} não encontrado.",
        )

    if id_admin is not None and not await buscar_administrador(id_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {id_admin} não encontrado.",
        )

    if id_lote is not None and not await buscar_lote(id_lote):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )


@router.post("/", response_model=AplicacaoRead, status_code=status.HTTP_201_CREATED)
async def criar_aplicacao(dados: AplicacaoCreate):
    """Registra uma nova aplicação de vacina."""
    await validar_referencias_aplicacao(
        id_paciente=dados.id_paciente,
        id_profissional=dados.id_profissional,
        id_admin=dados.id_admin,
        id_lote=dados.id_lote,
    )

    proximo_id = await obter_proximo_id_aplicacao()

    dados_dict = dados.model_dump()

    if dados_dict.get("data") is None:
        dados_dict["data"] = datetime.now(timezone.utc)

    aplicacao = Aplicacao(
        id_aplicacao=proximo_id,
        **dados_dict,
    )

    await aplicacao.insert()

    return aplicacao


@router.get("/", response_model=Page[AplicacaoReadDetalhada])
async def listar_aplicacoes(
    order_by: str = Query(
        "data",
        enum=["data", "id_aplicacao", "local", "id_paciente", "id_profissional"],
    ),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista aplicações cadastradas com paginação e ordenação."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Aplicacao.find_all().sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/por-paciente/{id_paciente}", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_paciente(
    id_paciente: PydanticObjectId,
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista aplicações realizadas em um paciente específico."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Aplicacao.find({"id_paciente": id_paciente}).sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/por-profissional/{id_profissional}", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_profissional(
    id_profissional: PydanticObjectId,
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista aplicações realizadas por um profissional de saúde específico."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Aplicacao.find({"id_profissional": id_profissional}).sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/por-data", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_data(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista aplicações realizadas dentro de um intervalo de datas."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    inicio = datetime.combine(data_inicio, time.min, tzinfo=timezone.utc)
    fim = datetime.combine(data_fim, time.max, tzinfo=timezone.utc)

    query = Aplicacao.find(
        {
            "data": {
                "$gte": inicio,
                "$lte": fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/por-ano", response_model=Page[AplicacaoReadDetalhada])
async def listar_por_ano(
    ano: int = Query(...),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista aplicações realizadas em um determinado ano."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    inicio = datetime(ano, 1, 1, tzinfo=timezone.utc)
    fim = datetime(ano + 1, 1, 1, tzinfo=timezone.utc)

    query = Aplicacao.find(
        {
            "data": {
                "$gte": inicio,
                "$lt": fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/por-local", response_model=Page[AplicacaoReadDetalhada])
async def buscar_por_local(
    local: str = Query(...),
    order_by: str = Query("data", enum=["data", "id_aplicacao", "local"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Busca aplicações pelo local usando pesquisa parcial e case-insensitive."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Aplicacao.find(
        {
            "local": {
                "$regex": local,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_aplicacoes(query, params)


@router.get("/total", response_model=dict)
async def contar_aplicacoes():
    """Retorna a quantidade total de aplicações cadastradas."""
    total = await Aplicacao.find_all().count()

    return {"total_aplicacoes": total}


@router.get("/contagem-por-lote", response_model=list[dict])
async def contagem_por_lote(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Conta quantas aplicações foram feitas por lote."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": "$id_lote",
                "total_aplicacoes": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "id_lote": "$_id",
                "total_aplicacoes": 1,
            }
        },
        {
            "$sort": {
                "total_aplicacoes": direcao,
            }
        },
    ]

    resultado = await Aplicacao.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/contagem-por-vacina", response_model=list[dict])
async def contagem_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Conta aplicações por vacina usando a relação entre aplicação, lote e vacina."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$lookup": {
                "from": "lotes",
                "localField": "id_lote",
                "foreignField": "id_lote",
                "as": "lote",
            }
        },
        {
            "$unwind": "$lote",
        },
        {
            "$group": {
                "_id": "$lote.codigo_vacina",
                "total_aplicacoes": {"$sum": 1},
            }
        },
        {
            "$lookup": {
                "from": "vacinas",
                "localField": "_id",
                "foreignField": "codigo_vacina",
                "as": "vacina",
            }
        },
        {
            "$unwind": {
                "path": "$vacina",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$project": {
                "_id": 0,
                "codigo_vacina": "$_id",
                "nome_vacina": "$vacina.nome",
                "total_aplicacoes": 1,
            }
        },
        {
            "$sort": {
                "total_aplicacoes": direcao,
            }
        },
    ]

    resultado = await Aplicacao.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/contagem-por-profissional", response_model=list[dict])
async def contagem_por_profissional(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Conta quantas aplicações foram realizadas por cada profissional de saúde."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": "$id_profissional",
                "total_aplicacoes": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "id_profissional": "$_id",
                "total_aplicacoes": 1,
            }
        },
        {
            "$sort": {
                "total_aplicacoes": direcao,
            }
        },
    ]

    resultado = await Aplicacao.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/{id_aplicacao}", response_model=AplicacaoReadDetalhada)
async def obter_aplicacao(id_aplicacao: int):
    """Busca uma aplicação pelo seu identificador numérico."""
    aplicacao = await Aplicacao.find_one({"id_aplicacao": id_aplicacao})

    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )

    return await montar_aplicacao_detalhada(aplicacao)


@router.patch("/{id_aplicacao}", response_model=AplicacaoRead)
async def atualizar_aplicacao(
    id_aplicacao: int,
    dados: AplicacaoUpdate,
):
    """Atualiza parcialmente os dados de uma aplicação existente."""
    aplicacao = await Aplicacao.find_one({"id_aplicacao": id_aplicacao})

    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )

    await validar_referencias_aplicacao(
        id_paciente=dados.id_paciente,
        id_profissional=dados.id_profissional,
        id_admin=dados.id_admin,
        id_lote=dados.id_lote,
    )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(aplicacao, campo, valor)

    await aplicacao.save()

    return aplicacao


@router.delete("/{id_aplicacao}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_aplicacao(id_aplicacao: int):
    """Remove uma aplicação pelo seu identificador numérico."""
    aplicacao = await Aplicacao.find_one({"id_aplicacao": id_aplicacao})

    if not aplicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação {id_aplicacao} não encontrada.",
        )

    await aplicacao.delete()
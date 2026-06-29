from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.lote import Lote
from app.models.vacina import Vacina
from app.schemas.lote import LoteCreate, LoteRead, LoteReadComVacina, LoteUpdate
from app.schemas.vacina import VacinaResumo

router = APIRouter(prefix="/lotes", tags=["Lotes"])


def obter_campo_ordenacao(order_by: str, order: str) -> str:
    """Retorna o campo usado para ordenar a listagem de lotes."""
    campos = {
        "id_lote": "id_lote",
        "validade": "validade",
        "data_chegada": "data_chegada",
        "quantidade": "quantidade",
    }

    campo = campos.get(order_by, "id_lote")

    return f"-{campo}" if order == "desc" else campo


async def obter_proximo_id_lote() -> int:
    """Calcula o próximo identificador numérico para um lote."""
    lotes = await Lote.find_all().sort("-id_lote").limit(1).to_list()

    if not lotes or lotes[0].id_lote is None:
        return 1

    return lotes[0].id_lote + 1


async def montar_lote_com_vacina(lote: Lote) -> LoteReadComVacina:
    """Monta a resposta de um lote incluindo os dados resumidos da vacina associada."""
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


async def paginar_lotes(query, params: Params) -> Page[LoteReadComVacina]:
    """Aplica paginação manual em uma consulta de lotes com dados da vacina."""
    total = await query.count()

    lotes = (
        await query
        .skip((params.page - 1) * params.size)
        .limit(params.size)
        .to_list()
    )

    itens = []

    for lote in lotes:
        itens.append(await montar_lote_com_vacina(lote))

    return create_page(itens, total=total, params=params)


@router.post("/", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
async def criar_lote(dados: LoteCreate):
    """Cria um novo lote associado a uma vacina existente."""
    vacina = await Vacina.find_one({"codigo_vacina": dados.codigo_vacina})

    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{dados.codigo_vacina}' não encontrada.",
        )

    proximo_id = await obter_proximo_id_lote()

    lote = Lote(
        id_lote=proximo_id,
        **dados.model_dump(),
    )

    await lote.insert()

    return lote


@router.get("/", response_model=Page[LoteReadComVacina])
async def listar_lotes(
    order_by: str = Query(
        "id_lote",
        enum=["id_lote", "validade", "data_chegada", "quantidade"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista lotes cadastrados com paginação e ordenação."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Lote.find_all().sort(campo_ordenacao)

    return await paginar_lotes(query, params)


@router.get("/por-vacina", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_vacina(
    codigo_vacina: str = Query(...),
    order_by: str = Query(
        "validade",
        enum=["id_lote", "validade", "data_chegada", "quantidade"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista lotes associados a uma vacina específica."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Lote.find({"codigo_vacina": codigo_vacina}).sort(campo_ordenacao)

    return await paginar_lotes(query, params)


@router.get("/validade", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_validade(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    order_by: str = Query(
        "validade",
        enum=["id_lote", "validade", "data_chegada", "quantidade"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista lotes cuja validade está dentro de um intervalo de datas."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Lote.find(
        {
            "validade": {
                "$gte": data_inicio,
                "$lte": data_fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_lotes(query, params)


@router.get("/validade-por-ano", response_model=Page[LoteReadComVacina])
async def listar_lotes_por_ano_validade(
    ano: int = Query(...),
    order_by: str = Query(
        "validade",
        enum=["id_lote", "validade", "data_chegada", "quantidade"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista lotes que vencem em um determinado ano."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    inicio = date(ano, 1, 1)
    fim = date(ano, 12, 31)

    query = Lote.find(
        {
            "validade": {
                "$gte": inicio,
                "$lte": fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_lotes(query, params)


@router.get("/estoque-por-vacina", response_model=list[dict])
async def estoque_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Calcula a quantidade total de doses disponíveis agrupada por vacina."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": "$codigo_vacina",
                "quantidade_total": {"$sum": "$quantidade"},
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
                "quantidade_total": 1,
            }
        },
        {
            "$sort": {
                "quantidade_total": direcao,
            }
        },
    ]

    resultado = await Lote.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/contagem-por-vacina", response_model=list[dict])
async def contagem_lotes_por_vacina(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Conta quantos lotes existem para cada vacina."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": "$codigo_vacina",
                "total_lotes": {"$sum": 1},
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
                "total_lotes": 1,
            }
        },
        {
            "$sort": {
                "total_lotes": direcao,
            }
        },
    ]

    resultado = await Lote.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/{id_lote}", response_model=LoteReadComVacina)
async def obter_lote(id_lote: int):
    """Busca um lote pelo seu identificador numérico."""
    lote = await Lote.find_one({"id_lote": id_lote})

    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )

    return await montar_lote_com_vacina(lote)


@router.patch("/{id_lote}", response_model=LoteRead)
async def atualizar_lote(
    id_lote: int,
    dados: LoteUpdate,
):
    """Atualiza parcialmente os dados de um lote existente."""
    lote = await Lote.find_one({"id_lote": id_lote})

    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )

    if dados.codigo_vacina:
        vacina = await Vacina.find_one({"codigo_vacina": dados.codigo_vacina})

        if not vacina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacina '{dados.codigo_vacina}' não encontrada.",
            )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(lote, campo, valor)

    await lote.save()

    return lote


@router.delete("/{id_lote}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_lote(id_lote: int):
    """Remove um lote pelo seu identificador numérico."""
    lote = await Lote.find_one({"id_lote": id_lote})

    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} não encontrado.",
        )

    await lote.delete()
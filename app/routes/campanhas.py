from datetime import date

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params, create_page

from app.models.administrador import Administrador
from app.models.campanha import Campanha, CampanhaVacina
from app.models.vacina import Vacina
from app.schemas.administrador import AdministradorReadDetalhado
from app.schemas.campanha import (
    CampanhaCreate,
    CampanhaRead,
    CampanhaReadDetalhada,
    CampanhaUpdate,
    CampanhaVacinaCreate,
    CampanhaVacinaRead,
)
from app.schemas.vacina import VacinaResumo

router = APIRouter(prefix="/campanhas", tags=["Campanhas"])


def obter_campo_ordenacao(order_by: str, order: str) -> str:
    """Retorna o campo usado para ordenar a listagem de campanhas."""
    campos = {
        "data_inicio": "data_inicio",
        "data_fim": "data_fim",
        "nome_campanha": "nome_campanha",
        "id_campanha": "id_campanha",
    }

    campo = campos.get(order_by, "data_inicio")

    return f"-{campo}" if order == "desc" else campo


async def obter_proximo_id_campanha() -> int:
    """Calcula o próximo identificador numérico para uma campanha."""
    campanhas = await Campanha.find_all().sort("-id_campanha").limit(1).to_list()

    if not campanhas or campanhas[0].id_campanha is None:
        return 1

    return campanhas[0].id_campanha + 1


async def buscar_administrador(id_admin: PydanticObjectId):
    """Busca um administrador pelo seu identificador do MongoDB."""
    return await Administrador.get(id_admin)


async def montar_campanha_detalhada(campanha: Campanha) -> CampanhaReadDetalhada:
    """Monta a resposta detalhada de uma campanha com administrador e vacinas associadas."""
    admin = await buscar_administrador(campanha.id_admin)

    admin_resumo = None

    if admin:
        try:
            admin_resumo = AdministradorReadDetalhado.model_validate(admin)
        except Exception:
            admin_resumo = None

    associacoes = await CampanhaVacina.find(
        {"id_campanha": campanha.id_campanha}
    ).to_list()

    vacinas = []

    for associacao in associacoes:
        vacina = await Vacina.find_one({"codigo_vacina": associacao.codigo_vacina})

        if vacina:
            vacinas.append(VacinaResumo.model_validate(vacina))

    return CampanhaReadDetalhada(
        id_campanha=campanha.id_campanha,
        nome_campanha=campanha.nome_campanha,
        data_inicio=campanha.data_inicio,
        data_fim=campanha.data_fim,
        id_admin=campanha.id_admin,
        admin=admin_resumo,
        vacinas=vacinas,
    )


async def paginar_campanhas(query, params: Params) -> Page[CampanhaReadDetalhada]:
    """Aplica paginação manual em uma consulta de campanhas detalhadas."""
    total = await query.count()

    campanhas = (
        await query
        .skip((params.page - 1) * params.size)
        .limit(params.size)
        .to_list()
    )

    itens = []

    for campanha in campanhas:
        itens.append(await montar_campanha_detalhada(campanha))

    return create_page(itens, total=total, params=params)


@router.post("/", response_model=CampanhaRead, status_code=status.HTTP_201_CREATED)
async def criar_campanha(dados: CampanhaCreate):
    """Cria uma nova campanha associada a um administrador existente."""
    admin = await buscar_administrador(dados.id_admin)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrador {dados.id_admin} não encontrado.",
        )

    proximo_id = await obter_proximo_id_campanha()

    campanha = Campanha(
        id_campanha=proximo_id,
        **dados.model_dump(),
    )

    await campanha.insert()

    return campanha


@router.get("/", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas(
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "data_fim", "nome_campanha", "id_campanha"],
    ),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista campanhas cadastradas com paginação e ordenação."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Campanha.find_all().sort(campo_ordenacao)

    return await paginar_campanhas(query, params)


@router.get("/busca", response_model=Page[CampanhaReadDetalhada])
async def buscar_campanhas_por_nome(
    nome: str = Query(...),
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "nome_campanha", "id_campanha"],
    ),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Busca campanhas pelo nome usando pesquisa parcial e case-insensitive."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Campanha.find(
        {
            "nome_campanha": {
                "$regex": nome,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_campanhas(query, params)


@router.get("/por-ano", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_ano(
    ano: int = Query(...),
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "nome_campanha", "id_campanha"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista campanhas iniciadas em um determinado ano."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    inicio = date(ano, 1, 1)
    fim = date(ano, 12, 31)

    query = Campanha.find(
        {
            "data_inicio": {
                "$gte": inicio,
                "$lte": fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_campanhas(query, params)


@router.get("/por-periodo", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_periodo(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "nome_campanha", "id_campanha"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista campanhas iniciadas dentro de um intervalo de datas."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Campanha.find(
        {
            "data_inicio": {
                "$gte": data_inicio,
                "$lte": data_fim,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_campanhas(query, params)


@router.get("/total", response_model=dict)
async def contar_campanhas():
    """Retorna a quantidade total de campanhas cadastradas."""
    total = await Campanha.find_all().count()

    return {"total_campanhas": total}


@router.get("/contagem-por-ano", response_model=list[dict])
async def contagem_campanhas_por_ano(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Agrupa e conta campanhas pelo ano de início."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": {
                    "$year": "$data_inicio",
                },
                "total_campanhas": {
                    "$sum": 1,
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "ano": "$_id",
                "total_campanhas": 1,
            }
        },
        {
            "$sort": {
                "ano": direcao,
            }
        },
    ]

    resultado = await Campanha.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/contagem-vacinas-por-campanha", response_model=list[dict])
async def contagem_vacinas_por_campanha(
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Conta quantas vacinas estão associadas a cada campanha."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$lookup": {
                "from": "campanhas_vacinas",
                "localField": "id_campanha",
                "foreignField": "id_campanha",
                "as": "vacinas_associadas",
            }
        },
        {
            "$project": {
                "_id": 0,
                "id_campanha": 1,
                "nome_campanha": 1,
                "total_vacinas": {
                    "$size": "$vacinas_associadas",
                },
            }
        },
        {
            "$sort": {
                "total_vacinas": direcao,
            }
        },
    ]

    resultado = await Campanha.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/por-vacina/{codigo_vacina}", response_model=Page[CampanhaReadDetalhada])
async def listar_campanhas_por_vacina(
    codigo_vacina: str,
    order_by: str = Query(
        "data_inicio",
        enum=["data_inicio", "nome_campanha", "id_campanha"],
    ),
    order: str = Query("desc", enum=["asc", "desc"]),
    params: Params = Depends(),
):
    """Lista campanhas que possuem uma vacina específica associada."""
    associacoes = await CampanhaVacina.find(
        {"codigo_vacina": codigo_vacina}
    ).to_list()

    ids_campanhas = [associacao.id_campanha for associacao in associacoes]

    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Campanha.find(
        {
            "id_campanha": {
                "$in": ids_campanhas,
            }
        }
    ).sort(campo_ordenacao)

    return await paginar_campanhas(query, params)


@router.get("/{id_campanha}", response_model=CampanhaReadDetalhada)
async def obter_campanha(id_campanha: int):
    """Busca uma campanha pelo seu identificador numérico."""
    campanha = await Campanha.find_one({"id_campanha": id_campanha})

    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )

    return await montar_campanha_detalhada(campanha)


@router.patch("/{id_campanha}", response_model=CampanhaRead)
async def atualizar_campanha(
    id_campanha: int,
    dados: CampanhaUpdate,
):
    """Atualiza parcialmente os dados de uma campanha existente."""
    campanha = await Campanha.find_one({"id_campanha": id_campanha})

    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )

    if dados.id_admin is not None:
        admin = await buscar_administrador(dados.id_admin)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Administrador {dados.id_admin} não encontrado.",
            )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(campanha, campo, valor)

    await campanha.save()

    return campanha


@router.delete("/{id_campanha}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_campanha(id_campanha: int):
    """Remove uma campanha e suas associações com vacinas."""
    campanha = await Campanha.find_one({"id_campanha": id_campanha})

    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )

    await CampanhaVacina.find({"id_campanha": id_campanha}).delete()
    await campanha.delete()


@router.post(
    "/{id_campanha}/vacinas",
    response_model=CampanhaVacinaRead,
    status_code=status.HTTP_201_CREATED,
)
async def adicionar_vacina_campanha(
    id_campanha: int,
    dados: CampanhaVacinaCreate,
):
    """Associa uma vacina existente a uma campanha existente."""
    campanha = await Campanha.find_one({"id_campanha": id_campanha})

    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )

    vacina = await Vacina.find_one({"codigo_vacina": dados.codigo_vacina})

    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{dados.codigo_vacina}' não encontrada.",
        )

    existente = await CampanhaVacina.find_one(
        {
            "id_campanha": id_campanha,
            "codigo_vacina": dados.codigo_vacina,
        }
    )

    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vacina já associada a esta campanha.",
        )

    associacao = CampanhaVacina(
        id_campanha=id_campanha,
        codigo_vacina=dados.codigo_vacina,
    )

    await associacao.insert()

    return associacao


@router.delete(
    "/{id_campanha}/vacinas/{codigo_vacina}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remover_vacina_campanha(
    id_campanha: int,
    codigo_vacina: str,
):
    """Remove a associação entre uma campanha e uma vacina."""
    associacao = await CampanhaVacina.find_one(
        {
            "id_campanha": id_campanha,
            "codigo_vacina": codigo_vacina,
        }
    )

    if not associacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associação não encontrada.",
        )

    await associacao.delete()
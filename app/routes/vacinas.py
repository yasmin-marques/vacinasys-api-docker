from fastapi import APIRouter, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate

from app.models.vacina import Vacina
from app.schemas.vacina import VacinaCreate, VacinaRead, VacinaUpdate

router = APIRouter(prefix="/vacinas", tags=["Vacinas"])


def obter_campo_ordenacao(order_by: str, order: str) -> str:
    """Retorna o campo usado para ordenar a listagem de vacinas."""
    campos = {
        "nome": "nome",
        "codigo_vacina": "codigo_vacina",
        "doenca": "doenca",
        "quantidade_doses": "quantidade_doses",
        "publico_alvo": "publico_alvo",
    }

    campo = campos.get(order_by, "nome")

    return f"-{campo}" if order == "desc" else campo


@router.post("/", response_model=VacinaRead, status_code=status.HTTP_201_CREATED)
async def criar_vacina(dados: VacinaCreate):
    """Cria uma nova vacina, evitando duplicidade pelo código."""
    existente = await Vacina.find_one({"codigo_vacina": dados.codigo_vacina})

    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vacina com código '{dados.codigo_vacina}' já existe.",
        )

    vacina = Vacina(**dados.model_dump())
    await vacina.insert()

    return vacina


@router.get("/", response_model=Page[VacinaRead])
async def listar_vacinas(
    order_by: str = Query(
        "nome",
        enum=["nome", "codigo_vacina", "doenca", "quantidade_doses", "publico_alvo"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
):
    """Lista vacinas cadastradas com paginação e ordenação."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)
    query = Vacina.find_all().sort(campo_ordenacao)

    return await paginate(query)


@router.get("/busca", response_model=Page[VacinaRead])
async def buscar_vacinas_por_nome(
    nome: str = Query(...),
    order_by: str = Query(
        "nome",
        enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
):
    """Busca vacinas pelo nome usando pesquisa parcial e case-insensitive."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Vacina.find(
        {
            "nome": {
                "$regex": nome,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginate(query)


@router.get("/por-doenca", response_model=Page[VacinaRead])
async def listar_vacinas_por_doenca(
    doenca: str = Query(...),
    order_by: str = Query(
        "nome",
        enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
):
    """Lista vacinas relacionadas a uma doença informada."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Vacina.find(
        {
            "doenca": {
                "$regex": doenca,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginate(query)


@router.get("/por-publico-alvo", response_model=Page[VacinaRead])
async def listar_vacinas_por_publico_alvo(
    publico: str = Query(...),
    order_by: str = Query(
        "nome",
        enum=["nome", "codigo_vacina", "doenca", "quantidade_doses"],
    ),
    order: str = Query("asc", enum=["asc", "desc"]),
):
    """Lista vacinas filtradas pelo público-alvo informado."""
    campo_ordenacao = obter_campo_ordenacao(order_by, order)

    query = Vacina.find(
        {
            "publico_alvo": {
                "$regex": publico,
                "$options": "i",
            }
        }
    ).sort(campo_ordenacao)

    return await paginate(query)


@router.get("/total", response_model=dict)
async def contar_vacinas():
    """Retorna a quantidade total de vacinas cadastradas."""
    total = await Vacina.find_all().count()

    return {"total_vacinas": total}


@router.get("/contagem-por-doses", response_model=list[dict])
async def contagem_vacinas_por_doses(
    order: str = Query("asc", enum=["asc", "desc"]),
):
    """Agrupa e conta vacinas pela quantidade de doses necessárias."""
    direcao = -1 if order == "desc" else 1

    pipeline = [
        {
            "$group": {
                "_id": "$quantidade_doses",
                "total_vacinas": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "quantidade_doses": "$_id",
                "total_vacinas": 1,
            }
        },
        {
            "$sort": {
                "quantidade_doses": direcao,
            }
        },
    ]

    resultado = await Vacina.get_motor_collection().aggregate(pipeline).to_list(length=None)

    return resultado


@router.get("/{codigo_vacina}", response_model=VacinaRead)
async def obter_vacina(codigo_vacina: str):
    """Busca uma vacina pelo seu código."""
    vacina = await Vacina.find_one({"codigo_vacina": codigo_vacina})

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
):
    """Atualiza parcialmente os dados de uma vacina existente."""
    vacina = await Vacina.find_one({"codigo_vacina": codigo_vacina})

    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{codigo_vacina}' não encontrada.",
        )

    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        setattr(vacina, campo, valor)

    await vacina.save()

    return vacina


@router.delete("/{codigo_vacina}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_vacina(codigo_vacina: str):
    """Remove uma vacina pelo seu código."""
    vacina = await Vacina.find_one({"codigo_vacina": codigo_vacina})

    if not vacina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vacina '{codigo_vacina}' não encontrada.",
        )

    await vacina.delete()
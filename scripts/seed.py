import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from beanie import PydanticObjectId, init_beanie
from faker import Faker
from minio import Minio
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.config import settings
from app.models.administrador import Administrador
from app.models.aplicacao import Aplicacao
from app.models.campanha import Campanha, CampanhaVacina
from app.models.document import Document
from app.models.lote import Lote
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.usuario import Usuario
from app.models.vacina import Vacina

fake = Faker("pt_BR")

mongo_client: AsyncIOMotorClient | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def gerar_telefone() -> str:
    return fake.phone_number()[:20]


def gerar_email_unico() -> str:
    return f"{uuid.uuid4().hex[:10]}@example.com"


def filtrar_campos(modelo, dados: dict) -> dict:
    campos = getattr(modelo, "model_fields", {})

    if not campos:
        return dados

    return {campo: valor for campo, valor in dados.items() if campo in campos}


def criar_documento(modelo, **dados):
    documento = modelo(**filtrar_campos(modelo, dados))

    if hasattr(documento, "id") and getattr(documento, "id", None) is None:
        documento.id = PydanticObjectId()

    return documento


async def inserir_varios(documentos: list):
    if not documentos:
        return documentos

    modelo = type(documentos[0])
    await modelo.insert_many(documentos)

    return documentos


async def init_database_seed() -> None:
    global mongo_client

    mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    database = mongo_client[settings.mongodb_database]

    await init_beanie(
        database=database,
        document_models=[
            Usuario,
            Administrador,
            Paciente,
            ProfissionalSaude,
            Vacina,
            Lote,
            Campanha,
            CampanhaVacina,
            Aplicacao,
            Document,
        ],
    )


async def close_database_seed() -> None:
    if mongo_client is not None:
        mongo_client.close()


async def limpar_banco() -> None:
    modelos = [
        Document,
        Aplicacao,
        CampanhaVacina,
        Campanha,
        Lote,
        Vacina,
        Administrador,
        Paciente,
        ProfissionalSaude,
        Usuario,
    ]

    for modelo in modelos:
        await modelo.find_all().delete()


async def criar_usuarios(quantidade: int = 300):
    usuarios = []

    fake.unique.clear()

    for _ in range(quantidade):
        usuario = Usuario(
            pnome=fake.first_name(),
            unome=fake.last_name(),
            email=gerar_email_unico(),
            senha=fake.password(length=12),
            telefone=gerar_telefone(),
            cpf_usuario=fake.unique.cpf(),
        )

        if getattr(usuario, "id", None) is None:
            usuario.id = PydanticObjectId()

        usuarios.append(usuario)

    await inserir_varios(usuarios)

    return usuarios


async def criar_administradores(usuarios: list[Usuario]):
    administradores = []

    for usuario in usuarios[:100]:
        administrador = Administrador(usuario_id=usuario.id)

        if getattr(administrador, "id", None) is None:
            administrador.id = PydanticObjectId()

        administradores.append(administrador)

    await inserir_varios(administradores)

    return administradores


async def criar_pacientes(usuarios: list[Usuario]):
    pacientes = []

    for usuario in usuarios[100:200]:
        paciente = Paciente(usuario_id=usuario.id)

        if getattr(paciente, "id", None) is None:
            paciente.id = PydanticObjectId()

        pacientes.append(paciente)

    await inserir_varios(pacientes)

    return pacientes


async def criar_profissionais(usuarios: list[Usuario]):
    profissionais = []

    formacoes = [
        "Enfermagem",
        "Técnico em Enfermagem",
        "Medicina",
        "Farmácia",
        "Biomedicina",
    ]

    for usuario in usuarios[200:300]:
        profissional = ProfissionalSaude(
            usuario_id=usuario.id,
            grau_formacao=random.choice(formacoes),
        )

        if getattr(profissional, "id", None) is None:
            profissional.id = PydanticObjectId()

        profissionais.append(profissional)

    await inserir_varios(profissionais)

    return profissionais


async def criar_vacinas(quantidade: int = 100):
    vacinas = []

    catalogo = [
        ("BCG", "Tuberculose", "Recém-nascidos", 1),
        ("Hepatite B", "Hepatite B", "Recém-nascidos e adultos", 3),
        ("VIP", "Poliomielite", "Crianças", 3),
        ("Tríplice Viral", "Sarampo, Caxumba e Rubéola", "Crianças e adultos", 2),
        ("Influenza", "Gripe", "Idosos, gestantes e crianças", 1),
        ("COVID-19", "COVID-19", "População geral", 2),
        ("HPV", "HPV", "Adolescentes", 2),
        ("Febre Amarela", "Febre Amarela", "Viajantes e áreas de risco", 1),
    ]

    fake.unique.clear()

    for _ in range(quantidade):
        nome, doenca, publico_alvo, quantidade_doses = random.choice(catalogo)

        vacina = criar_documento(
            Vacina,
            codigo_vacina=fake.unique.bothify(text="VAC-#####"),
            nome=nome,
            doenca=doenca,
            quantidade_doses=quantidade_doses,
            publico_alvo=publico_alvo,
            cnpj_fabricante=fake.cnpj(),
        )

        vacinas.append(vacina)

    await inserir_varios(vacinas)

    return vacinas


async def criar_lotes(vacinas: list[Vacina], quantidade: int = 100):
    lotes = []

    for indice in range(1, quantidade + 1):
        vacina = random.choice(vacinas)
        data_chegada = fake.date_between(start_date="-1y", end_date="today")
        validade = data_chegada + timedelta(days=fake.random_int(min=180, max=900))

        lote = criar_documento(
            Lote,
            id_lote=indice,
            validade=validade,
            data_chegada=data_chegada,
            quantidade=fake.random_int(min=50, max=2000),
            cnpj_fornecedor=fake.cnpj(),
            codigo_vacina=vacina.codigo_vacina,
        )

        lotes.append(lote)

    await inserir_varios(lotes)

    return lotes


async def criar_campanhas(
    administradores: list[Administrador],
    vacinas: list[Vacina],
    quantidade: int = 100,
):
    campanhas = []
    vacinas_por_campanha = []

    for indice in range(1, quantidade + 1):
        data_inicio = fake.date_between(start_date="-1y", end_date="+6m")
        data_fim = data_inicio + timedelta(days=fake.random_int(min=15, max=90))
        administrador = random.choice(administradores)

        campanha = criar_documento(
            Campanha,
            id_campanha=indice,
            nome_campanha=f"Campanha {fake.word().capitalize()} {fake.random_int(min=2024, max=2026)}",
            data_inicio=data_inicio,
            data_fim=data_fim,
            id_admin=administrador.id,
        )

        quantidade_vacinas = fake.random_int(min=1, max=3)
        vacinas_sorteadas = random.sample(vacinas, quantidade_vacinas)

        campanhas.append(campanha)
        vacinas_por_campanha.append((campanha, vacinas_sorteadas))

    await inserir_varios(campanhas)

    vinculos = []

    for campanha, vacinas_sorteadas in vacinas_por_campanha:
        for vacina in vacinas_sorteadas:
            vinculo = criar_documento(
                CampanhaVacina,
                id_campanha=campanha.id_campanha,
                codigo_vacina=vacina.codigo_vacina,
            )

            vinculos.append(vinculo)

    await inserir_varios(vinculos)

    return campanhas


async def criar_aplicacoes(
    pacientes: list[Paciente],
    profissionais: list[ProfissionalSaude],
    administradores: list[Administrador],
    lotes: list[Lote],
    quantidade: int = 100,
):
    aplicacoes = []

    locais = [
        "UBS Centro",
        "Posto de Saúde Vila Nova",
        "Hospital Municipal",
        "Unidade Básica de Saúde São José",
        "Centro de Imunização",
    ]

    for indice in range(1, quantidade + 1):
        paciente = random.choice(pacientes)
        profissional = random.choice(profissionais)
        administrador = random.choice(administradores)
        lote = random.choice(lotes)

        aplicacao = criar_documento(
            Aplicacao,
            id_aplicacao=indice,
            data=fake.date_time_between(
                start_date="-1y",
                end_date="now",
                tzinfo=timezone.utc,
            ),
            id_paciente=paciente.id,
            id_profissional=profissional.id,
            id_admin=administrador.id,
            id_lote=lote.id_lote,
            local=random.choice(locais),
        )

        aplicacoes.append(aplicacao)

    await inserir_varios(aplicacoes)

    return aplicacoes


def criar_cliente_minio() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def garantir_bucket_minio(client: Minio) -> None:
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def enviar_arquivo_minio(
    client: Minio,
    object_name: str,
    conteudo: bytes,
    content_type: str,
) -> None:
    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        data=BytesIO(conteudo),
        length=len(conteudo),
        content_type=content_type,
    )


async def criar_documents(campanhas: list[Campanha], quantidade: int = 100):
    documentos = []

    tipos = [
        ("pdf", "application/pdf", "Relatorio"),
        ("pdf", "application/pdf", "Autorizacao"),
        ("pdf", "application/pdf", "Protocolo"),
        ("png", "image/png", "Cartaz"),
        ("png", "image/png", "Banner"),
    ]

    conteudos = {
        "pdf": (
            b"%PDF-1.4\n1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj "
            b"2 0 obj<</Type /Pages /Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox[0 0 612 792]>>"
            b"endobj\nxref\n0 4\ntrailer<</Size 4 /Root 1 0 R>>\n"
            b"startxref\n0\n%%EOF"
        ),
        "png": (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
    }

    minio_client = criar_cliente_minio()
    minio_disponivel = True

    try:
        garantir_bucket_minio(minio_client)
    except Exception as erro:
        minio_disponivel = False
        print(
            "Aviso: não foi possível conectar ao MinIO. "
            f"Apenas os metadados serão inseridos. Detalhe: {erro}"
        )

    for _ in range(quantidade):
        extensao, content_type, prefixo = random.choice(tipos)
        campanha = random.choice(campanhas)
        conteudo = conteudos[extensao]
        document_id = PydanticObjectId()
        object_name = str(document_id)

        documento = criar_documento(
            Document,
            id=document_id,
            original_filename=f"{prefixo}_Campanha_{campanha.id_campanha}_{fake.random_int(min=1000, max=9999)}.{extensao}",
            content_type=content_type,
            extension=f".{extensao}",
            size_bytes=len(conteudo),
            created_at=utc_now(),
            campanha_id=str(campanha.id_campanha),
        )

        await documento.insert()

        if minio_disponivel:
            try:
                enviar_arquivo_minio(
                    minio_client,
                    object_name,
                    conteudo,
                    content_type,
                )
            except Exception as erro:
                print(f"Aviso: falha ao enviar {object_name} para o MinIO. Detalhe: {erro}")

        documentos.append(documento)

    return documentos


async def main():
    await init_database_seed()

    try:
        await limpar_banco()

        usuarios = await criar_usuarios(quantidade=300)
        administradores = await criar_administradores(usuarios)
        pacientes = await criar_pacientes(usuarios)
        profissionais = await criar_profissionais(usuarios)
        vacinas = await criar_vacinas(quantidade=100)
        lotes = await criar_lotes(vacinas, quantidade=100)
        campanhas = await criar_campanhas(administradores, vacinas, quantidade=100)
        aplicacoes = await criar_aplicacoes(
            pacientes,
            profissionais,
            administradores,
            lotes,
            quantidade=100,
        )
        documentos = await criar_documents(campanhas, quantidade=100)

        print(f"{len(usuarios)} usuários criados.")
        print(f"{len(administradores)} administradores criados.")
        print(f"{len(pacientes)} pacientes criados.")
        print(f"{len(profissionais)} profissionais criados.")
        print(f"{len(vacinas)} vacinas criadas.")
        print(f"{len(lotes)} lotes criados.")
        print(f"{len(campanhas)} campanhas criadas.")
        print(f"{len(aplicacoes)} aplicações criadas.")
        print(f"{len(documentos)} documentos criados.")
    finally:
        await close_database_seed()


if __name__ == "__main__":
    asyncio.run(main())
import sys
import uuid
import asyncio
from pathlib import Path
from datetime import timedelta

# Adiciona a raiz do projeto ao path para permitir imports da pasta app
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from faker import Faker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import engine
from app.config import UPLOAD_DIR

from app.models.usuario import Usuario
from app.models.administrador import Administrador
from app.models.paciente import Paciente
from app.models.profissional_saude import ProfissionalSaude
from app.models.vacina import Vacina
from app.models.lote import Lote
from app.models.campanha import Campanha, CampanhaVacina
from app.models.aplicacao import Aplicacao
from app.models.document import Document

fake = Faker("pt_BR")


# cria usuarios base que serão associados posteriormente
async def criar_usuarios(session: AsyncSession, quantidade: int = 300):
    usuarios = []

    for _ in range(quantidade):
        usuario = Usuario(
            pnome=fake.first_name(),
            unome=fake.last_name(),
            email=f"{uuid.uuid4().hex[:10]}@example.com",
            senha=fake.password(length=12),
            telefone=fake.phone_number(),
            cpf_usuario=fake.unique.cpf(),
        )

        session.add(usuario)
        usuarios.append(usuario)

    # Gera os IDs sem finalizar a transação
    await session.flush()

    return usuarios


# os 100 primeiros usuarios serão administradores
async def criar_administradores(
    session: AsyncSession,
    usuarios: list[Usuario]
):
    administradores = []

    for usuario in usuarios[:100]:
        admin = Administrador(
            id_admin=usuario.id_usuario
        )

        session.add(admin)
        administradores.append(admin)

    await session.flush()

    return administradores


# os próximos 100 usuarios serão pacientes
async def criar_pacientes(
    session: AsyncSession,
    usuarios: list[Usuario]
):
    pacientes = []

    for usuario in usuarios[100:200]:
        paciente = Paciente(
            id_paciente=usuario.id_usuario
        )

        session.add(paciente)
        pacientes.append(paciente)

    await session.flush()

    return pacientes


# os últimos 100 usuarios serão profissionais de saúde
async def criar_profissionais(
    session: AsyncSession,
    usuarios: list[Usuario]
):
    profissionais = []

    for usuario in usuarios[200:300]:
        profissional = ProfissionalSaude(
            id_profissional=usuario.id_usuario,
            grau_formacao=fake.random_element(
                elements=[
                    "Enfermeiro(a)",
                    "Técnico(a) de Enfermagem",
                    "Médico(a)",
                    "Farmacêutico(a)",
                    "Biomédico(a)",
                ]
            ),
        )

        session.add(profissional)
        profissionais.append(profissional)

    await session.flush()

    return profissionais


# cria vacinas com dados coerentes para campanhas de imunização
async def criar_vacinas(
    session: AsyncSession,
    quantidade: int = 100
):
    vacinas = []

    doencas = [
        ("BCG", "Tuberculose", "Recém-nascidos"),
        ("Hepatite B", "Hepatite B", "Recém-nascidos e adultos"),
        ("VIP", "Poliomielite", "Crianças"),
        ("Tríplice Viral", "Sarampo, Caxumba e Rubéola", "Crianças e adultos"),
        ("Influenza", "Gripe", "Idosos, gestantes e crianças"),
        ("COVID-19", "COVID-19", "População geral"),
        ("HPV", "HPV", "Adolescentes"),
        ("Febre Amarela", "Febre Amarela", "Viajantes e áreas de risco"),
    ]

    for _ in range(quantidade):
        nome, doenca, publico = fake.random_element(doencas)

        vacina = Vacina(
            codigo_vacina=fake.unique.bothify(text="VAC-#####"),
            nome=f"{nome} {fake.bothify(text='LT-####')}",
            doenca=doenca,
            publico_alvo=publico,
            quantidade_doses=fake.random_int(min=1, max=5),
            cnpj_fabricante=fake.cnpj(),
        )

        session.add(vacina)
        vacinas.append(vacina)

    await session.flush()

    return vacinas


# cria lotes vinculados as vacinas já cadastradas
async def criar_lotes(
    session: AsyncSession,
    vacinas: list[Vacina],
    quantidade: int = 100
):
    lotes = []

    for _ in range(quantidade):
        vacina = fake.random_element(vacinas)

        lote = Lote(
            validade=fake.future_date(end_date="+2y"),
            data_chegada=fake.date_between(
                start_date="-1y",
                end_date="today"
            ),
            quantidade=fake.random_int(min=50, max=2000),
            cnpj_fornecedor=fake.cnpj(),
            codigo_vacina=vacina.codigo_vacina,
        )

        session.add(lote)
        lotes.append(lote)

    await session.flush()

    return lotes


# cria campanhas administradas por usuarios administradores
async def criar_campanhas(
    session: AsyncSession,
    administradores: list[Administrador],
    vacinas: list[Vacina],
    quantidade: int = 100,
):
    campanhas = []

    for _ in range(quantidade):
        inicio = fake.date_between(
            start_date="-1y",
            end_date="+6m"
        )

        fim = inicio + timedelta(
            days=fake.random_int(min=15, max=90)
        )

        campanha = Campanha(
            nome_campanha=(
                f"Campanha "
                f"{fake.word().capitalize()} "
                f"{fake.random_int(min=2024, max=2026)}"
            ),
            data_inicio=inicio,
            data_fim=fim,
            id_admin=fake.random_element(administradores).id_admin,
        )

        session.add(campanha)
        campanhas.append(campanha)

    await session.flush()

    # cria relacionamento muitos-para-muitos entre campanhas e vacinas
    for campanha in campanhas:
        vacinas_sorteadas = fake.random_elements(
            elements=vacinas,
            length=fake.random_int(min=1, max=3),
            unique=True,
        )

        for vacina in vacinas_sorteadas:
            session.add(
                CampanhaVacina(
                    id_campanha=campanha.id_campanha,
                    codigo_vacina=vacina.codigo_vacina,
                )
            )

    await session.flush()

    return campanhas


# cria aplicações de vacina utilizando os lotes cadastrados
async def criar_aplicacoes(
    session: AsyncSession,
    pacientes: list[Paciente],
    profissionais: list[ProfissionalSaude],
    administradores: list[Administrador],
    lotes: list[Lote],
    quantidade: int = 100,
):
    aplicacoes = []

    for _ in range(quantidade):
        aplicacao = Aplicacao(
            data=fake.date_time_between(
                start_date="-1y",
                end_date="now"
            ),
            id_paciente=fake.random_element(pacientes).id_paciente,
            id_profissional=fake.random_element(profissionais).id_profissional,
            id_admin=fake.random_element(administradores).id_admin,
            id_lote=fake.random_element(lotes).id_lote,
            local=fake.random_element(
                elements=[
                    "UBS Centro",
                    "Posto de Saúde Vila Nova",
                    "Hospital Municipal",
                    "Unidade Básica de Saúde São José",
                    "Centro de Imunização",
                ]
            ),
        )

        session.add(aplicacao)
        aplicacoes.append(aplicacao)

    await session.flush()

    return aplicacoes


async def criar_documents(
    session: AsyncSession,
    campanhas: list[Campanha],
    quantidade: int = 100,
):
    """
    Cria registros de Document vinculados a campanhas e grava arquivos
    dummy no disco para que o banco e o sistema de arquivos fiquem
    consistentes entre si.

    Tipos simulados: PDF (relatórios/autorizações) e PNG (cartazes/banners).
    """
    documentos = []

    tipos = [
        ("pdf", "application/pdf", "Relatório"),
        ("pdf", "application/pdf", "Autorização"),
        ("pdf", "application/pdf", "Protocolo"),
        ("png", "image/png", "Cartaz"),
        ("png", "image/png", "Banner"),
    ]

    # Conteúdo mínimo válido para cada tipo, assim o arquivo existe em disco
    # e não é um arquivo vazio (evita problemas em downloads de teste).
    _conteudo = {
        "pdf": (
            b"%PDF-1.4\n1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj "
            b"2 0 obj<</Type /Pages /Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox[0 0 612 792]>>"
            b"endobj\nxref\n0 4\ntrailer<</Size 4 /Root 1 0 R>>\n"
            b"startxref\n0\n%%EOF"
        ),
        # PNG de 1x1 pixel transparente (cabeçalho mínimo válido)
        "png": (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
    }

    for _ in range(quantidade):
        ext, content_type, prefixo = fake.random_element(tipos)
        campanha = fake.random_element(campanhas)

        # Nome de arquivo realista
        sufixo = fake.bothify(text="??##").upper()
        original_filename = (
            f"{prefixo}_{campanha.nome_campanha.replace(' ', '_')}_{sufixo}.{ext}"
        )

        conteudo = _conteudo[ext]

        document = Document(
            original_filename=original_filename,
            content_type=content_type,
            extension=ext,
            size_bytes=len(conteudo),
            id_campanha=campanha.id_campanha,
        )

        session.add(document)
        await session.flush()  # garante que document.id está disponível

        # Grava o arquivo físico em disco
        file_path = UPLOAD_DIR / f"{document.id}.{ext}"
        file_path.write_bytes(conteudo)

        documentos.append(document)

    return documentos


async def main():
    async with AsyncSession(engine) as session:

        usuarios = await criar_usuarios(
            session,
            quantidade=300
        )

        administradores = await criar_administradores(
            session,
            usuarios
        )

        pacientes = await criar_pacientes(
            session,
            usuarios
        )

        profissionais = await criar_profissionais(
            session,
            usuarios
        )

        vacinas = await criar_vacinas(
            session,
            quantidade=100
        )

        lotes = await criar_lotes(
            session,
            vacinas,
            quantidade=100
        )

        campanhas = await criar_campanhas(
            session,
            administradores,
            vacinas,
            quantidade=100
        )

        aplicacoes = await criar_aplicacoes(
            session,
            pacientes,
            profissionais,
            administradores,
            lotes,
            quantidade=100,
        )

        documentos = await criar_documents(
            session,
            campanhas,
            quantidade=100,
        )

        # commit único ao final para persistir todos os dados
        await session.commit()

        print(f"{len(usuarios)} usuários criados.")
        print(f"{len(administradores)} administradores criados.")
        print(f"{len(pacientes)} pacientes criados.")
        print(f"{len(profissionais)} profissionais criados.")
        print(f"{len(vacinas)} vacinas criadas.")
        print(f"{len(lotes)} lotes criados.")
        print(f"{len(campanhas)} campanhas criadas.")
        print(f"{len(aplicacoes)} aplicações criadas.")
        print(f"{len(documentos)} documentos criados.")


if __name__ == "__main__":
    asyncio.run(main())
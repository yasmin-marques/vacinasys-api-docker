
"""Rotas para gerenciamento de Documentos vinculados a Campanhas."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import UPLOAD_DIR
from app.database import get_session
from app.models.campanha import Campanha
from app.models.document import Document
from app.schemas.document import DocumentRead, DocumentReadDetalhado
from app.service.document_service import save_document_file, delete_document_file

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _query_detalhada():
    return select(Document).options(selectinload(Document.campanha))


@router.post(
    "/upload/{id_campanha}",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documento(
    id_campanha: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Faz upload de um arquivo e o vincula a uma campanha."""
    campanha = await session.get(Campanha, id_campanha)
    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo '{file.content_type}' não permitido.",
        )

    content = await file.read()
    size_bytes = len(content)

    if size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo permitido: {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    original_filename = file.filename or "arquivo"
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""

    document = Document(
        original_filename=original_filename,
        content_type=file.content_type,
        extension=extension,
        size_bytes=size_bytes,
        id_campanha=id_campanha,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    await save_document_file(content, document.id, extension)

    return document


@router.get("/", response_model=Page[DocumentReadDetalhado])
async def listar_documentos(
    order_by: str = Query(
        "created_at",
        enum=["created_at", "id", "original_filename", "size_bytes"],
        description="Campo de ordenação",
    ),
    order: str = Query("desc", enum=["asc", "desc"], description="Direção da ordenação"),
    session: AsyncSession = Depends(get_session),
):
    """Lista todos os documentos com dados da campanha e ordenação."""
    colunas = {
        "created_at": Document.created_at,
        "id": Document.id,
        "original_filename": Document.original_filename,
        "size_bytes": Document.size_bytes,
    }
    coluna = colunas.get(order_by, Document.created_at)
    query = _query_detalhada().order_by(
        coluna.desc() if order == "desc" else coluna.asc()
    )
    return await paginate(session, query)


@router.get("/por-campanha/{id_campanha}", response_model=Page[DocumentReadDetalhado])
async def listar_por_campanha(
    id_campanha: int,
    order_by: str = Query("created_at", enum=["created_at", "id", "original_filename", "size_bytes"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    session: AsyncSession = Depends(get_session),
):
    """Lista todos os documentos de uma campanha específica."""
    campanha = await session.get(Campanha, id_campanha)
    if not campanha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {id_campanha} não encontrada.",
        )
    colunas = {
        "created_at": Document.created_at,
        "id": Document.id,
        "original_filename": Document.original_filename,
        "size_bytes": Document.size_bytes,
    }
    coluna = colunas.get(order_by, Document.created_at)
    query = (
        _query_detalhada()
        .where(Document.id_campanha == id_campanha)
        .order_by(coluna.desc() if order == "desc" else coluna.asc())
    )
    return await paginate(session, query)


@router.get("/{id_document}", response_model=DocumentReadDetalhado)
async def obter_documento(
    id_document: int,
    session: AsyncSession = Depends(get_session),
):
    """Obtém os metadados de um documento pelo ID."""
    resultado = await session.exec(
        _query_detalhada().where(Document.id == id_document)
    )
    document = resultado.first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {id_document} não encontrado.",
        )
    return document


@router.get("/{id_document}/download")
async def download_documento(
    id_document: int,
    session: AsyncSession = Depends(get_session),
):
    """Faz o download do arquivo de um documento."""
    document = await session.get(Document, id_document)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {id_document} não encontrado.",
        )

    file_path = UPLOAD_DIR / f"{document.id}.{document.extension}"

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado no servidor.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=document.content_type,
        filename=document.original_filename,
    )


@router.put("/{id_document}", response_model=DocumentRead)
async def substituir_documento(
    id_document: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Substitui o arquivo físico de um documento e atualiza seus metadados."""
    document = await session.get(Document, id_document)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {id_document} não encontrado.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo '{file.content_type}' não permitido.",
        )

    content = await file.read()
    size_bytes = len(content)

    if size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo permitido: {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # Apaga o arquivo antigo (extensão pode ser diferente do novo)
    await delete_document_file(f"{document.id}.{document.extension}")

    original_filename = file.filename or "arquivo"
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""

    document.original_filename = original_filename
    document.content_type = file.content_type
    document.extension = extension
    document.size_bytes = size_bytes

    session.add(document)
    await session.commit()
    await session.refresh(document)

    await save_document_file(content, document.id, extension)

    return document


@router.delete("/{id_document}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_documento(
    id_document: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove um documento (registro no banco e arquivo físico)."""
    document = await session.get(Document, id_document)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {id_document} não encontrado.",
        )

    await delete_document_file(f"{document.id}.{document.extension}")

    await session.delete(document)
    await session.commit()

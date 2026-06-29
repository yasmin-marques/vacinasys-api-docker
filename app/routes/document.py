from beanie import PydanticObjectId
from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate

from app.schemas.document import DocumentRead
from app.service.document_service import DocumentService

router = APIRouter(tags=["Documents"])

service = DocumentService()


# 1. UPLOAD DE DOCUMENTO
# POST /campanhas/{campanha_id}/documents
@router.post(
    "/campanhas/{campanha_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    campanha_id: str,
    file: UploadFile = File(...),
):
    """Envia um novo documento e o associa a uma campanha."""
    return await service.upload_document(campanha_id=campanha_id, file=file)


# 2. LISTAR DOCUMENTOS DE UMA CAMPANHA (paginado)
# GET /campanhas/{campanha_id}/documents
@router.get(
    "/campanhas/{campanha_id}/documents",
    response_model=Page[DocumentRead],
)
async def list_documents(campanha_id: str):
    """Lista, de forma paginada, os documentos de uma campanha."""
    return await paginate(service.list_documents_query(campanha_id))


# 3. BUSCAR METADADOS DO DOCUMENTO
# GET /documents/{document_id}
@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document_metadata(document_id: PydanticObjectId):
    """Retorna os metadados de um documento."""
    return await service.get_document(document_id)


# 4. DOWNLOAD DO ARQUIVO (STREAMING)
# GET /documents/{document_id}/download
@router.get("/documents/{document_id}/download")
async def download_document(document_id: PydanticObjectId):
    """Baixa ou exibe o arquivo físico armazenado no MinIO."""
    response, document = await service.download_document(document_id)

    return StreamingResponse(
        response,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}"'
        },
    )


# 5. SUBSTITUIR ARQUIVO
# PUT /documents/{document_id}
@router.put("/documents/{document_id}", response_model=DocumentRead)
async def replace_document(
    document_id: PydanticObjectId,
    file: UploadFile = File(...),
):
    """Substitui o arquivo físico e atualiza os metadados do documento."""
    return await service.replace_document(document_id=document_id, file=file)


# 6. REMOVER DOCUMENTO
# DELETE /documents/{document_id}
@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: PydanticObjectId):
    """Remove os metadados (MongoDB) e o arquivo físico (MinIO)."""
    await service.delete_document(document_id)
    return {"message": "Documento removido com sucesso."}
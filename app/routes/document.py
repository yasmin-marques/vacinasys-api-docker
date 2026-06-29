from fastapi import APIRouter, UploadFile, File, status
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
from app.service.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

service = DocumentService()


# 1. UPLOAD DE DOCUMENTO
@router.post(
    "/campanhas/{campanha_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    campanha_id: str,
    file: UploadFile = File(...),
):
    return await service.upload_document(
        campanha_id=campanha_id,
        file=file,
    )


# 2. LISTAR DOCUMENTOS DE UMA CAMPANHA
@router.get("/campanhas/{campanha_id}/documents")
async def list_documents(
    campanha_id: str,
):
    return await service.list_documents(campanha_id)


# 3. BUSCAR METADADOS DO DOCUMENTO
# Removida a rota conflitante anterior e corrigido o nome da função/serviço
@router.get("/documents/{document_id}")
async def get_document_metadata(
    document_id: PydanticObjectId,
):
    return await service.get_document(document_id)


# 4. DOWNLOAD DO ARQUIVO (STREAMING)
# Transforma o retorno do service em um StreamingResponse com os headers corretos
@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: PydanticObjectId,
):
    response, document = await service.download_document(document_id)

    return StreamingResponse(
        response,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}"'
        },
    )


# 5. SUBSTITUIR ARQUIVO
@router.put("/documents/{document_id}")
async def replace_document(
    document_id: PydanticObjectId,
    file: UploadFile = File(...),
):
    return await service.replace_document(
        document_id=document_id,
        file=file,
    )


# 6. REMOVER DOCUMENTO
# Agora retorna um JSON de sucesso estruturado em vez de None
@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: PydanticObjectId
):
    await service.delete_document(document_id)

    return {"message": "Documento removido com sucesso."}
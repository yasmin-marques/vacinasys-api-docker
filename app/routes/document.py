from fastapi import APIRouter, UploadFile, File

from app.service.document_service import DocumentService

router = APIRouter(
    prefix="",
    tags=["Documents"],
)

service = DocumentService()

# UPLOAD
@router.post("/campanhas/{campanha_id}/documents")
async def upload_document(
    campanha_id: str,
    file: UploadFile = File(...),
):
    return await service.upload_document(
        campanha_id=campanha_id,
        file=file,
    )


# LISTAR DOCUMENTOS DE UMA CAMPANHA

@router.get("/campanhas/{campanha_id}/documents")
async def list_documents(
    campanha_id: str,
):
    return await service.list_documents(campanha_id)


# BUSCAR METADADOS
@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
):
    return await service.get_document_metadata(document_id)



# DOWNLOADS
@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
):
    return await service.download_document(document_id)



# SUBSTITUIR ARQUIVO
@router.put("/documents/{document_id}")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
):
    return await service.replace_document(
        document_id=document_id,
        file=file,
    )

# REMOVER DOCUMENTO
@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
):
    return await service.delete_document(document_id)


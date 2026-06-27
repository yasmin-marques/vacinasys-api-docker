from fastapi import UploadFile

from app.service.minio_service import MinioService


class DocumentService:

    def __init__(self):
        self.minio = MinioService()


    async def upload_document(
        self,
        campanha_id: str,
        file: UploadFile,
    ):
        """
        Salva os metadados do documento no MongoDB e o arquivo no MinIO.
        """
        raise NotImplementedError


    async def list_documents(
        self,
        campanha_id: str,
    ):
        """
        Lista todos os documentos associados a uma campanha.
        """
        raise NotImplementedError


    async def get_document_metadata(
        self,
        document_id: str,
    ):
        """
        Retorna apenas os metadados do documento.
        """
        raise NotImplementedError


    async def download_document(
        self,
        document_id: str,
    ):
        """
        Retorna o arquivo armazenado no MinIO.
        """
        raise NotImplementedError


    async def replace_document(
        self,
        document_id: str,
        file: UploadFile,
    ):
        """
        Substitui o arquivo físico e atualiza seus metadados.
        """
        raise NotImplementedError


    async def delete_document(
        self,
        document_id: str,
    ):
        """
        Remove o documento do MongoDB e o arquivo do MinIO.
        """
        raise NotImplementedError
    
document_service = DocumentService()
# Fluxo esperado
#     Route
#     │
#     ▼
# UploadFile
#     │
#     ▼
# DocumentService
#     │
#     ├── extrai:
#     │      • nome original
#     │      • extensão
#     │      • MIME
#     │      • tamanho
#     │
#     ├── cria Document
#     │
#     ├── salva no MongoDB
#     │
#     ├── usa o id gerado como object_name
#     │
#     ├── envia o arquivo ao MinIO
#     │
#     └── retorna os metadados
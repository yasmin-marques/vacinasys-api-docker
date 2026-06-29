from pathlib import Path
from fastapi import HTTPException, UploadFile, status

from app.models.document import Document
from app.service.minio_service import MinioService

from beanie import PydanticObjectId

class DocumentService:
    """
    Serviço responsável por coordenar a persistência dos metadados
    dos documentos no MongoDB e o armazenamento dos arquivos no MinIO.
    """

    def __init__(self):
        self.minio = MinioService()

    async def upload_document(
        self,
        campanha_id: str,
        file: UploadFile,
    ) -> Document:
        """
        Envia um novo documento para uma campanha com tratamento robusto de erros e rollback.
        """
        # 1. Validações Iniciais (Fail Fast)
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo inválido."
            )

        if not file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo MIME inválido."
            )

        # 2. Extração do tamanho do arquivo de forma segura
        try:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não foi possível ler o arquivo: {str(e)}"
            )

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo está vazio."
            )

        # 3. Criação e Persistência dos Metadados (MongoDB)
        try:
            document = Document(
                original_filename=file.filename,
                content_type=file.content_type,
                extension=Path(file.filename).suffix,
                size_bytes=size,
                campanha_id=campanha_id,
            )
            await document.insert()
        except Exception as e:
            # Erros de banco de dados durante a inserção
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar metadados no banco de dados: {str(e)}"
            )

        # 4. Envio do Arquivo (MinIO) com Rollback Dedicado
        try:
            self.minio.upload_file(
                object_name=str(document.id),
                data=file.file,
                size=size,
                content_type=file.content_type,
            )
            return document
        except Exception as minio_error:
            # Rollback cirúrgico: se o MinIO falhar, remove do MongoDB
            await document.delete()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Falha no armazenamento do arquivo físico. Upload cancelado: {str(minio_error)}"
            )

    async def get_document(
        self,
        document_id: PydanticObjectId,
    ) -> Document:
        """
        Retorna os metadados de um documento.

        Levanta:
            HTTPException(404): caso o documento não exista.
        """

        document = await Document.get(document_id)

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento não encontrado."
            )

        return document

    def list_documents_query(self, campanha_id: str):
        """
        Monta a query dos documentos de uma campanha.

        Retorna o objeto de consulta do Beanie (sem executá-lo) para que a
        rota aplique a paginação via fastapi-pagination, evitando carregar
        a coleção inteira de uma só vez.
        """

        return Document.find(
            Document.campanha_id == campanha_id
        ).sort("-created_at")

    async def download_document(
        self,
        document_id: PydanticObjectId,
    ):
        """
        Realiza o download do arquivo armazenado no MinIO.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Utilizar o id do documento como nome do objeto.
            3. Solicitar o arquivo ao MinIO.
            4. Retornar um StreamingResponse.
        """

        document = await self.get_document(document_id)

        response = self.minio.download_file(
            object_name=str(document.id)
        )

        return response, document

    async def replace_document(
        self,
        document_id: PydanticObjectId,
        file: UploadFile,
    ) -> Document:
        """
        Substitui o arquivo associado a um documento.
        """

        document = await self.get_document(document_id)

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo inválido."
            )

        if not file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo MIME inválido."
            )

        try:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não foi possível ler o arquivo: {e}"
        )

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo está vazio."
            )

        try:
            self.minio.upload_file(
                object_name=str(document.id),
                data=file.file,
                size=size,
                content_type=file.content_type,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erro ao substituir arquivo no MinIO: {e}"
            )

        document.original_filename = file.filename
        document.content_type = file.content_type
        document.extension = Path(file.filename).suffix
        document.size_bytes = size

        await document.save()

        return document
    
    async def delete_document(
        self,
        document_id: PydanticObjectId,
    ):
        """
        Remove um documento.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Remover o arquivo físico do MinIO.
            3. Remover os metadados do MongoDB.
        """

        document = await self.get_document(document_id)

        try:
            self.minio.delete_file(str(document.id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Não foi possível remover o arquivo do MinIO."
            )
        await document.delete()
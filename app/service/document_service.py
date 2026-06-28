from fastapi import HTTPException, UploadFile

from app.service.minio_service import MinioService


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
    ):
        """
        Envia um novo documento para uma campanha.

        Fluxo esperado:
            1. Verificar se a campanha existe.
            2. Extrair os metadados do UploadFile.
            3. Criar um Document.
            4. Persistir os metadados no MongoDB.
            5. Utilizar o id gerado como nome físico do arquivo.
            6. Enviar o arquivo ao MinIO.
            7. Retornar os metadados do documento.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )

    async def list_documents(
        self,
        campanha_id: str,
    ):
        """
        Lista todos os documentos associados a uma campanha.

        Fluxo esperado:
            1. Verificar se a campanha existe.
            2. Consultar os documentos da campanha no MongoDB.
            3. Retornar a lista de metadados.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )

    async def get_document_metadata(
        self,
        document_id: str,
    ):
        """
        Retorna apenas os metadados de um documento.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Retornar seus metadados.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )

    async def download_document(
        self,
        document_id: str,
    ):
        """
        Realiza o download do arquivo armazenado no MinIO.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Utilizar o id do documento como nome do objeto.
            3. Solicitar o arquivo ao MinIO.
            4. Retornar um StreamingResponse.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )

    async def replace_document(
        self,
        document_id: str,
        file: UploadFile,
    ):
        """
        Substitui o arquivo associado a um documento.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Remover o arquivo antigo do MinIO.
            3. Enviar o novo arquivo utilizando o mesmo id.
            4. Atualizar os metadados.
            5. Salvar novamente o documento.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )

    async def delete_document(
        self,
        document_id: str,
    ):
        """
        Remove um documento.

        Fluxo esperado:
            1. Buscar o documento no MongoDB.
            2. Remover o arquivo físico do MinIO.
            3. Remover os metadados do MongoDB.
        """

        raise HTTPException(
            status_code=501,
            detail="Endpoint em desenvolvimento."
        )
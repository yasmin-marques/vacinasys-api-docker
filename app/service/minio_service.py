from minio import Minio
from minio.error import S3Error
from app.config import settings
from typing import BinaryIO

import logging

logger = logging.getLogger(__name__)


client = Minio(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)

class MinioService:

    def __init__(self):
        self.client = client
        self.bucket = settings.minio_bucket


    def initialize(self):
        try:
            # 2. Check if the bucket exists using bucket_exists()
            if self.client.bucket_exists(self.bucket):
                logger.info("Bucket '%s' já existe.", self.bucket)
            else:
                # 3. Create the bucket using make_bucket() if it does not exist
                self.client.make_bucket(self.bucket)
                logger.info("Bucket '%s' criado com sucesso.", self.bucket)

        except S3Error:
            logger.exception("Erro ao inicializar o bucket do MinIO.")
            raise

    def upload_file(
        self, 
        object_name: str,
        data: BinaryIO,
        size: int,
        content_type: str
    ) -> None:
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=data,
                length=size,
                content_type=content_type
            )
            logger.info(
                "Arquivo %s enviado para o bucket %s.",
                object_name,
                self.bucket,
            )
        except S3Error:
            logger.exception("Erro ao enviar arquivo para o MinIO.")
            raise
        

    # não fazemos leitura dos bytes;    
    # get_object() devolve um objeto de resposta (HTTPResponse do cliente MinIO) que permite fazer streaming
    def download_file(self, object_name: str):
        try:
            return self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
        except S3Error:
            logger.exception("Erro ao fazer download do arquivo")
            raise

    def delete_file(self, object_name: str) -> None:
        try:
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_name,
            )
            logger.info(
                "Arquivo %s removido do bucket %s.",
                object_name,
                self.bucket,
            )
        except S3Error:
            logger.exception("Erro ao deletar o arquivo")
            raise

    def file_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            return True
        except S3Error:
            return False
        
    def replace_file(self, 
            object_name: str,
            data: BinaryIO,
            size: int,
            content_type: str):

        self.delete_file(object_name=object_name)

        self.upload_file(
            object_name,
            data,
            size,
            content_type
        )
        
        
minio_service = MinioService()
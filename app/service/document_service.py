# app/service/document_service.py
import aiofiles
import aiofiles.os

from app.config import UPLOAD_DIR  # UPLOAD_DIR já é Path absoluto; o mkdir é feito lá


async def save_document_file(
    content: bytes,
    document_id: int,
    extension: str,
) -> tuple[str, str]:
    """
    Salva os bytes do arquivo em disco de forma assíncrona.

    Recebe `content` (bytes já lidos no router) em vez do objeto UploadFile,
    para não bloquear o event loop com I/O síncrono.

    Retorna (stored_filename, file_path).
    """
    stored_filename = f"{document_id}.{extension}"
    file_path = UPLOAD_DIR / stored_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return stored_filename, str(file_path)


async def delete_document_file(stored_filename: str) -> None:
    """Remove o arquivo físico do disco de forma assíncrona."""
    file_path = UPLOAD_DIR / stored_filename

    try:
        await aiofiles.os.remove(file_path)
    except FileNotFoundError:
        pass  # já foi removido ou nunca chegou a existir — sem problema
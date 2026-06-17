from uuid import uuid4

from app.infrastructure.storage.client import get_minio_client
from app.infrastructure.storage.minio_storage import MinioStorage


async def upload_pdf(file_bytes: bytes, user_id: str):
    client = get_minio_client()
    storage = MinioStorage(client)

    object_name = f"{user_id}/{uuid4()}.pdf"

    await storage.upload(
        bucket_name="knowledge",
        object_name=object_name,
        data=file_bytes,
    )

    return object_name

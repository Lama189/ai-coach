import asyncio
from datetime import timedelta
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from app.application.interfaces.object_storage import IObjectStorage


class MinioStorage(IObjectStorage):
    def __init__(self, client: Minio):
        self._client = client


    async def upload(self, bucket_name: str, object_name: str, data: bytes) -> str:
        def sync_put():
            self._ensure_bucket(bucket_name)
            self._client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type="application/pdf",
            )
            
            return object_name

        return await asyncio.to_thread(sync_put)


    async def download(self, bucket: str, object_name: str) -> bytes:
        response = self._client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


    async def delete(self, bucket: str, object_name: str) -> None:
        self._client.remove_object(bucket, object_name)


    async def get_upload_url(self, bucket_name: str, object_name: str, expires_minutes: int = 15) -> str:
        def sync_action():
            self._ensure_bucket(bucket_name)

            return self._client.presigned_put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(minutes=expires_minutes),
            )
        
        return await asyncio.to_thread(sync_action)
    

    def _ensure_bucket(self, bucket_name: str) -> None:
        if not self._client.bucket_exists(bucket_name):
            self._client.make_bucket(bucket_name)
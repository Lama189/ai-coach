import asyncio
from datetime import timedelta
from io import BytesIO
from minio import Minio
from urllib.parse import quote, unquote

from app.application.interfaces.object_storage import IObjectStorage


class MinioStorage(IObjectStorage):
    def __init__(self, client: Minio):
        self._client = client


    async def upload(
        self, 
        bucket_name: str, 
        object_name: str, 
        data: bytes,
        filename: str | None = None
    ) -> str:
        def sync_put():
            self._ensure_bucket(bucket_name)

            safe_filename = quote(filename) if filename else None
            metadata = {"X-Amz-Meta-Original-Name": safe_filename} if safe_filename else None
            
            self._client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type="application/pdf",
                metadata=metadata
            )
            
            return object_name

        return await asyncio.to_thread(sync_put)


    async def download(self, bucket: str, object_name: str) -> tuple[bytes, str | None]:
        def sync_download() -> tuple[bytes, str | None]:
            response = self._client.get_object(bucket, object_name)
            try:
            
                file_bytes = response.read()
                headers = response.headers or {}

                raw_filename = headers.get("x-amz-meta-original-name")
                filename = unquote(raw_filename) if raw_filename else None
                
                return file_bytes, filename
            finally:
                response.close()
                response.release_conn()
                
        return await asyncio.to_thread(sync_download)


    async def delete(self, bucket: str, object_name: str) -> None:
        def sync_delete():
            self._client.remove_object(bucket, object_name)
        return await asyncio.to_thread(sync_delete)


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
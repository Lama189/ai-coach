from abc import ABC, abstractmethod


class IObjectStorage(ABC):

    @abstractmethod
    async def upload(
        self, 
        bucket_name: str, 
        object_name: str, 
        data: bytes,
        filename: str | None = None
    ) -> str:
        ...
    
    @abstractmethod
    async def download(self, bucket: str, object_name: str) -> tuple[bytes, str | None]:
        ...

    
    @abstractmethod
    async def delete(self, bucket: str, object_name: str) -> None:
        ...

    
    @abstractmethod
    async def get_upload_url(self, bucket_name: str, object_name: str, expires_minutes: int = 15) -> str:
        raise NotImplementedError
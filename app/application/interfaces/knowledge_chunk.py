from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.knowledge.chunk import KnowledgeChunk


class IKnowledgeChunkRepository(ABC):

    @abstractmethod
    async def save(self, chunk: KnowledgeChunk) -> None:
        ...

    @abstractmethod
    async def search_by(
        self,
        document_id: UUID | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 50,
    ) -> list[KnowledgeChunk]:
        ...

    @abstractmethod
    async def delete(self, chunk_id: UUID) -> None:
        ...

    @abstractmethod
    async def delete_by_document_id(self, document_id: UUID) -> None:
        ...

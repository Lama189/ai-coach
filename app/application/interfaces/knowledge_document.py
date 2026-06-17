from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.knowledge.document import Document
from app.domain.enums import KnowledgeDocumentStatus


class IKnowledgeDocumentRepository(ABC):

    @abstractmethod
    async def save(self, document: Document) -> None:
        ...

    @abstractmethod
    async def search_by(
        self,
        uploaded_by: UUID | None = None,
        status: KnowledgeDocumentStatus | None = None,
        filename: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        ...

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        ...

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.knowledge.document import Document
from app.domain.enums import KnowledgeDocumentStatus
from app.application.interfaces.knowledge_document import IKnowledgeDocumentRepository
from app.infrastructure.postgres.models.document import KnowledgeDocument as KnowledgeDocumentModel


class PostgresKnowledgeDocumentRepository(IKnowledgeDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session


    async def save(self, document: Document) -> None:
        existing = await self._session.get(KnowledgeDocumentModel, document.id)

        if existing is None:
            model = self._to_model(document)
            self._session.add(model)
        else:
            existing.title = document.title
            existing.filename = document.filename
            existing.bucket = document.bucket
            existing.object_name = document.object_name
            existing.uploaded_by = document.uploaded_by
            existing.status = document.status.value

        await self._session.flush()


    async def search_by(
        self,
        uploaded_by: UUID | None = None,
        status: KnowledgeDocumentStatus | None = None,
        filename: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        stmt = select(KnowledgeDocumentModel)

        if uploaded_by is not None:
            stmt = stmt.where(KnowledgeDocumentModel.uploaded_by == uploaded_by)

        if status is not None:
            stmt = stmt.where(KnowledgeDocumentModel.status == status.value)

        if filename is not None:
            stmt = stmt.where(KnowledgeDocumentModel.filename.ilike(f"%{filename}%"))

        stmt = stmt.order_by(KnowledgeDocumentModel.id.desc()).limit(limit).offset(offset)

        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]


    async def delete(self, document_id: UUID) -> None:
        model = await self._session.get(KnowledgeDocumentModel, document_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()


    def _to_domain(self, model: KnowledgeDocumentModel) -> Document:
        return Document(
            id=model.id,
            title=model.title,
            filename=model.filename,
            bucket=model.bucket,
            object_name=model.object_name,
            uploaded_by=model.uploaded_by,
            status=KnowledgeDocumentStatus(model.status),
        )


    def _to_model(self, document: Document) -> KnowledgeDocumentModel:
        return KnowledgeDocumentModel(
            id=document.id,
            title=document.title,
            filename=document.filename,
            bucket=document.bucket,
            object_name=document.object_name,
            uploaded_by=document.uploaded_by,
            status=document.status.value,
        )

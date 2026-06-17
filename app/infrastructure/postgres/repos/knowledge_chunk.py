from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.knowledge.chunk import KnowledgeChunk
from app.application.interfaces.knowledge_chunk import IKnowledgeChunkRepository
from app.infrastructure.postgres.models.chunk import KnowledgeChunk as KnowledgeChunkModel


class PostgresKnowledgeChunkRepository(IKnowledgeChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session


    async def save(self, chunk: KnowledgeChunk) -> None:
        existing = await self._session.get(KnowledgeChunkModel, chunk.id)

        if existing is None:
            model = self._to_model(chunk)
            self._session.add(model)
        else:
            existing.document_id = chunk.document_id
            existing.chunk_index = chunk.chunk_index
            existing.content = chunk.content
            existing.embedding = chunk.embedding
            existing.token_count = chunk.token_count
            existing.content_hash = chunk.content_hash
            existing.meta = chunk.meta

        await self._session.flush()


    async def search_by(
        self,
        document_id: UUID | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 50,
    ) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunkModel)

        if document_id is not None:
            stmt = stmt.where(KnowledgeChunkModel.document_id == document_id)

        if query_embedding is not None:
            stmt = stmt.order_by(
                KnowledgeChunkModel.embedding.cosine_distance(query_embedding)
            )
        else:
            stmt = stmt.order_by(
                KnowledgeChunkModel.document_id,
                KnowledgeChunkModel.chunk_index,
            )

        stmt = stmt.limit(limit)

        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]


    async def delete(self, chunk_id: UUID) -> None:
        model = await self._session.get(KnowledgeChunkModel, chunk_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def delete_by_document_id(self, document_id: UUID) -> None:
        stmt = select(KnowledgeChunkModel).where(
            KnowledgeChunkModel.document_id == document_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        for model in models:
            await self._session.delete(model)
        await self._session.flush()


    def _to_domain(self, model: KnowledgeChunkModel) -> KnowledgeChunk:
        return KnowledgeChunk(
            id=model.id,
            document_id=model.document_id,
            chunk_index=model.chunk_index,
            content=model.content,
            embedding=model.embedding,
            token_count=model.token_count,
            content_hash=model.content_hash,
            meta=model.meta,
        )


    def _to_model(self, chunk: KnowledgeChunk) -> KnowledgeChunkModel:
        return KnowledgeChunkModel(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            embedding=chunk.embedding,
            token_count=chunk.token_count,
            content_hash=chunk.content_hash,
            meta=chunk.meta,
        )

from uuid import UUID

from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.domain.identity.insight import UserInsight
from app.application.dto.identity import CreateInsightDTO
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService


class InsightService:
    def __init__(self, uow: IUnitOfWork, embedder: SentenceTransformerEmbeddingService) -> None:
        self._uow = uow
        self._embedder = embedder

    
    async def create_insight(self, user_id: UUID, dto: CreateInsightDTO) -> UserInsight:
        embedding = await self._embedder.get_embedding(f"{dto.tag.value} {dto.content}")

        insight = UserInsight(
            user_id=user_id,
            content=dto.content,
            tag=dto.tag
        )

        await self._uow.insights.save(insight, embedding)
        await self._uow.commit()
        return insight
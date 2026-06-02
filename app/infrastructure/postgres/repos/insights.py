from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.insight import UserInsight
from app.domain.interfaces.insights import IUserInsightRepository
from app.infrastructure.postgres.models.insights import UserInsight as UserInsightModel


class PostgresUserInsightRepository(IUserInsightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    
    async def save(self, insight: UserInsight) -> None:
        stmt = select(UserInsightModel).where(UserInsightModel.id == insight.id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            model = UserInsightModel(
                id=insight.id,
                user_id=insight.user_id,
                content=insight.content,
                embedding=insight.embedding
            )
            self._session.add(model)
        else:
            existing.content = insight.content
            existing.embedding = insight.embedding

        await self._session.flush()


    async def search_by_vector(self, user_id: UUID, query_embedding: list[float], limit: int = 3) -> list[UserInsight]:
        stmt = (
            select(UserInsightModel)
            .where(UserInsightModel.user_id == user_id)
            .order_by(UserInsightModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        models = (await self._session.execute(stmt)).scalars().all()

        return [
            UserInsight(
                id=m.id,
                user_id=m.user_id,
                content=m.content,
                embedding=m.embedding
            )
            for m in models
        ]
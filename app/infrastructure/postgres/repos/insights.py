from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.insight import UserInsight
from app.domain.enums import InsightTag
from app.domain.interfaces.insights import IUserInsightRepository
from app.infrastructure.postgres.models.insights import UserInsight as UserInsightModel


class PostgresUserInsightRepository(IUserInsightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    
    async def save(self, insight: UserInsight, embedding: list[float] | None = None) -> None:
        stmt = select(UserInsightModel).where(UserInsightModel.id == insight.id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            model = UserInsightModel(
                id=insight.id,
                user_id=insight.user_id,
                content=insight.content,
                tag=insight.tag,
                embedding=embedding
            )
            self._session.add(model)
        else:
            existing.content = insight.content
            existing.tag = insight.tag
            if embedding:
                existing.embedding = embedding

        await self._session.flush()


    async def search_by(
        self, user_id: UUID | None, 
        query_embedding: list[float] | None = None, 
        tags: list[InsightTag] | None = None,
        limit: int = 3
    ) -> list[UserInsight]:
        stmt = select(UserInsightModel)

        if user_id is not None:
            stmt = stmt.where(UserInsightModel.user_id == user_id)


        if tags is not None:
            stmt = stmt.where(UserInsightModel.tag.in_(tags))

        if query_embedding is not None:
            stmt = stmt.order_by(UserInsightModel.embedding.cosine_distance(query_embedding))
        else:
            stmt = stmt.order_by(UserInsightModel.id.desc())


        stmt = stmt.limit(limit)

        models = (await self._session.execute(stmt)).scalars().all()

        return [
            UserInsight(
                id=m.id,
                user_id=m.user_id,
                content=m.content,
                tag=m.tag,
            )
            for m in models
        ]
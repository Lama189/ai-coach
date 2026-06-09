from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.intents import UserIntent
from app.domain.interfaces.intents import IUserIntentRepository
from app.infrastructure.postgres.models.intents import UserIntentModel


class PostgresUserIntentRepository(IUserIntentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, intent: UserIntent, embedding: list[float] | None = None) -> None:
        model = UserIntentModel(
            id=intent.id,
            user_id=intent.user_id,
            goal=intent.goal,
            constraints=intent.constraints,
            focus_areas=[f.value for f in intent.focus_areas],
            location=intent.location.value,
            context=intent.context,
            embedding=embedding,
            program_id=intent.program_id,
        )
        self._session.add(model)
        await self._session.flush()


    async def find_similar(
        self,
        user_id: UUID,
        query_embedding: list[float],
        threshold: float = 0.92,
        limit: int = 1,
    ) -> UserIntent | None:
        stmt = (
            select(UserIntentModel)
            .where(UserIntentModel.user_id == user_id)
            .order_by(UserIntentModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None

        distance = await self._get_distance(model, query_embedding)
        similarity = 1 - distance
        if similarity < threshold:
            return None

        return self._to_domain(model)


    async def _get_distance(self, model: UserIntentModel, query_embedding: list[float]) -> float:
        stmt = select(
            UserIntentModel.embedding.cosine_distance(query_embedding)
        ).where(UserIntentModel.id == model.id)

        result = await self._session.execute(stmt)
        return result.scalar_one()


    async def get_by_user(self, user_id: UUID) -> list[UserIntent]:
        stmt = (
            select(UserIntentModel)
            .where(UserIntentModel.user_id == user_id)
            .order_by(UserIntentModel.created_at.desc())
        )
        
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]


    def _to_domain(self, model: UserIntentModel) -> UserIntent:
        return UserIntent(
            id=model.id,
            user_id=model.user_id,
            goal=model.goal,
            constraints=model.constraints,
            focus_areas=model.focus_areas,
            location=model.location,
            context=model.context,
            program_id=model.program_id,
        )
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup
from app.application.interfaces.exercises import IExerciseRepository
from app.infrastructure.postgres.models.exercises import Exercise as ExerciseModel


def normalize(name: str) -> str:
    return name.strip().lower()


class PostgresExerciseRepository(IExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_exercise(self, exercise: Exercise, embedding: list[float] | None = None) -> None:
        stmt = select(ExerciseModel).where(
            ExerciseModel.name.ilike(f"%{normalize(exercise.name)}%")
        )

        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(exercise)
            self._session.add(model)

            if embedding:
                model.embedding = embedding
        else:
            existing.muscle_group = exercise.muscle_group
            existing.description = str(exercise.description)

            if embedding:
                existing.embedding = embedding


    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        stmt = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
    

    async def search(
        self,
        query: str | None = None,
        muscle_group: MuscleGroup | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Exercise]:
        stmt = select(ExerciseModel)

        if query:
            stmt = stmt.where(ExerciseModel.name.ilike(f"%{query}%"))

        if muscle_group:
            stmt = stmt.where(ExerciseModel.muscle_group == muscle_group)

        stmt = stmt.order_by(ExerciseModel.muscle_group).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]
    

    async def get_by_name(self, name: str) -> Exercise | None:
        stmt = select(ExerciseModel).where(
            ExerciseModel.name.ilike(f"%{normalize(name)}%")
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_domain(model) if model else None
    

    async def get_by_ids(self, exercise_ids: list[UUID]) -> list[Exercise]:
        if not exercise_ids:
            return []

        stmt = select(ExerciseModel).where(ExerciseModel.id.in_(exercise_ids))

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]
    

    async def find_familiar(
        self,
        embedding: list[float],
        threshold: float = 0.85,
    ) -> Exercise | None:
        stmt = (
            select(ExerciseModel)
            .where(
                ExerciseModel.embedding.cosine_distance(embedding)
                <= (1 - threshold)
            )
            .order_by(
                ExerciseModel.embedding.cosine_distance(embedding)
            )
            .limit(1)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)


    def _to_model(self, exercise: Exercise) -> ExerciseModel:
        return ExerciseModel(
            id=exercise.id,
            name=exercise.name,
            muscle_group=exercise.muscle_group.value, 
            description=exercise.description,
        )


    def _to_domain(self, model: ExerciseModel) -> Exercise:
        return Exercise(
            name=model.name,
            muscle_group=MuscleGroup(model.muscle_group),  
            id=model.id,
            description=model.description,
        )
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup, MovementPattern
from app.application.interfaces.exercises import IExerciseRepository
from app.infrastructure.postgres.models.exercises import Exercise as ExerciseModel


def normalize(name: str) -> str:
    return name.strip().lower()


class PostgresExerciseRepository(IExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by(self, **kwargs) -> Exercise | None:
        stmt = select(ExerciseModel).filter_by(**kwargs)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None


    async def save_exercise(self, exercise: Exercise, embedding: list[float] | None = None) -> None:
        stmt = select(ExerciseModel).where(ExerciseModel.name.ilike(normalize(exercise.name)))
        result = await self._session.execute(stmt)
        existing = result.scalars().first()

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


    async def delete(self, exercise_id: UUID) -> None:
        model = await self._session.get(ExerciseModel, exercise_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    
    async def search_relevant(
        self,
        muscle_groups: list[str],
        excluded_patterns: list[str],
        excluded_equipment: list[str],
        embedding: list[float] | None,
        limit: int,
    ) -> list[Exercise]:

        stmt = select(ExerciseModel).where(
            ExerciseModel.muscle_group.in_(muscle_groups)
        )

        if excluded_patterns:
            stmt = stmt.where(
                ~ExerciseModel.movement_patterns.op("&&")(excluded_patterns)
            )

        if excluded_equipment:
            stmt = stmt.where(
                ExerciseModel.equipment.notin_(excluded_equipment)
            )

        if embedding:
            stmt = stmt.order_by(
                ExerciseModel.embedding.cosine_distance(embedding)
            )
        else:
            stmt = stmt.order_by(ExerciseModel.muscle_group)

        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]


    def _to_model(self, exercise: Exercise) -> ExerciseModel:
        return ExerciseModel(
            id=exercise.id,
            name=exercise.name,
            muscle_group=exercise.muscle_group.value,
            equipment=exercise.equipment,
            movement_patterns=[p.value for p in exercise.movement_patterns],
            description=exercise.description,
        )


    def _to_domain(self, model: ExerciseModel) -> Exercise:
        return Exercise(
            name=model.name,
            muscle_group=MuscleGroup(model.muscle_group),
            equipment=model.equipment,
            movement_patterns=[MovementPattern(p) for p in model.movement_patterns],
            id=model.id,
            description=model.description,
        )
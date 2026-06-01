from uuid import UUID
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup
from app.domain.interfaces.exercises import IExerciseRepository
from app.infrastructure.postgres.models.exercises import Exercise as ExerciseModel


class PostgresExerciseRepository(IExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    
    async def save_exercise(self, exercise: Exercise) -> None:
        existing = await self._session.get(ExerciseModel, exercise.id)

        if existing is None:
            model = self._to_model(exercise)
            self._session.add(model)
        else:
            existing.name = exercise.name
            existing.muscle_group = exercise.muscle_group
            existing.description = str(exercise.description)

        await self._session.flush()


    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        stmt = (select(ExerciseModel).where(ExerciseModel.id == exercise_id))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
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
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(model) for model in models]


    async def exists(self, exercise_name: str) -> bool:
        stmt = select(exists().where(ExerciseModel.name == exercise_name))
        return (await self._session.execute(stmt)).scalar_one()
    

    async def get_by_ids(self, exercise_ids: list[UUID]) -> list[Exercise]:
        if not exercise_ids:
            return []
        
        stmt = select(ExerciseModel).where(ExerciseModel.id.in_(exercise_ids))
        models = (await self._session.execute(stmt)).scalars().all()   

        return [self._to_domain(model) for model in models]                              


    def _to_domain(self, model: ExerciseModel) -> Exercise:
        return Exercise(
            name=model.name,
            muscle_group=model.muscle_group,
            id=model.id,
            description=model.description
        )
    

    def _to_model(self, model: Exercise) -> ExerciseModel:
        return ExerciseModel(
            id=model.id,
            name=model.name,
            muscle_group=model.muscle_group,
            description=model.description
        )

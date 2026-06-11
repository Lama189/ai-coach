from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.workout_day import WorkoutDay
from app.application.interfaces.workout_day import IWorkoutDayRepository
from app.infrastructure.postgres.models.workout_days import WorkoutDay as WorkoutDayModel


class PostgresWorkoutDayRepository(IWorkoutDayRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    
    async def save(self, workout_day: WorkoutDay, program_id: UUID) -> None:
        existing = await self._session.get(WorkoutDayModel, workout_day.id)

        if existing is None:
            model = self._to_model(workout_day, program_id)
            self._session.add(model)
        else:
            existing.day_number = workout_day.day_number
            existing.program_id = program_id
            existing.title = workout_day.title

        await self._session.flush()


    async def get_by_program_id(self, program_id: UUID) -> list[WorkoutDay]:
        stmt = select(WorkoutDayModel).where(WorkoutDayModel.program_id == program_id)
        
        models = (await self._session.execute(stmt)).scalars().all()
        if models is None:
            return []

        return [self._to_domain(model) for model in models]



    def _to_domain(self, model: WorkoutDayModel) -> WorkoutDay:
        return WorkoutDay(
            day_number=model.day_number,
            title=model.title,
            id=model.id
        )
    

    def _to_model(self, model: WorkoutDay, program_id: UUID) -> WorkoutDayModel:
        return WorkoutDayModel(
            id=model.id,
            program_id=program_id,
            day_number=model.day_number,
            title=model.title
        )


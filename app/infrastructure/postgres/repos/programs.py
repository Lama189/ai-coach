from uuid import UUID
from datetime import datetime
from sqlalchemy import select, exists, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.program import WorkoutProgram
from app.domain.interfaces.program import IWorkoutProgramRepository
from app.infrastructure.postgres.models.workout_programs import WorkoutProgram as WorkoutProgramModel


class PostgresWorkoutProgramRepository(IWorkoutProgramRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    
    async def save(self, program: WorkoutProgram) -> None:
        existing = await self._session.get(WorkoutProgramModel, program.id)

        if existing is None:
            model = self._to_model(program)
            self._session.add(model)
        else:
            existing.user_id = program.user_id
            existing.name = program.name
            existing.description = str(program.description)
            existing.is_active = program.is_active
            existing.updated_at = func.now()

    
    def _to_domain(self, model: WorkoutProgramModel) -> WorkoutProgram:
        return WorkoutProgram(
            user_id=model.user_id,
            name=model.name,
            is_active=model.is_active,
            id=model.id,
            description=model.description,
        )
    

    async def deactivate_all_for_user(self, user_id: UUID) -> None:
        stmt = (
            update(WorkoutProgramModel)
            .where(
                WorkoutProgramModel.user_id == user_id,
                WorkoutProgramModel.is_active == True
            )
            .values(
                is_active=False,
                updated_at=func.now()
            )
        )

        await self._session.execute(stmt)
    

    def _to_model(self, model: WorkoutProgram) -> WorkoutProgramModel:
        return WorkoutProgramModel(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            is_active=model.is_active
        )
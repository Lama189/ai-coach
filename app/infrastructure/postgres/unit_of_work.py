from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.database import async_session_maker

from app.application.interfaces.unit_of_work import IUnitOfWork

from app.infrastructure.postgres.repos.identity import PostgresUserRepository
from app.infrastructure.postgres.repos.exercises import PostgresExerciseRepository
from app.infrastructure.postgres.repos.programs import PostgresWorkoutProgramRepository
from app.infrastructure.postgres.repos.workout_days import PostgresWorkoutDayRepository
from app.infrastructure.postgres.repos.workout_day_exercises import PostgresWorkoutDayExerciseRepository
from app.infrastructure.postgres.repos.insights import PostgresUserInsightRepository
from app.infrastructure.postgres.repos.intents import PostgresUserIntentRepository


class PostgresUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "PostgresUnitOfWork":
        if self._session is None:
            self._session = async_session_maker()

        self.users = PostgresUserRepository(self._session)
        self.exercises = PostgresExerciseRepository(self._session)
        self.programs = PostgresWorkoutProgramRepository(self._session)
        self.workout_days = PostgresWorkoutDayRepository(self._session)
        self.workout_days_exercise = PostgresWorkoutDayExerciseRepository(self._session)
        self.insights = PostgresUserInsightRepository(self._session)
        self.intents = PostgresUserIntentRepository(self._session)

        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()

from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.database import async_session_maker

from app.domain.interfaces.identity import IUserRepository
from app.domain.interfaces.exercises import IExerciseRepository
from app.domain.interfaces.program import IWorkoutProgramRepository
from app.domain.interfaces.workout_day import IWorkoutDayRepository
from app.domain.interfaces.workout_day_exercise import IWorkoutDayExerciseRepository
from app.domain.interfaces.insights import IUserInsightRepository
from app.domain.interfaces.intents import IUserIntentRepository

from app.infrastructure.postgres.repos.identity import PostgresUserRepository
from app.infrastructure.postgres.repos.exercises import PostgresExerciseRepository
from app.infrastructure.postgres.repos.programs import PostgresWorkoutProgramRepository
from app.infrastructure.postgres.repos.workout_days import PostgresWorkoutDayRepository
from app.infrastructure.postgres.repos.workout_day_exercises import PostgresWorkoutDayExerciseRepository
from app.infrastructure.postgres.repos.insights import PostgresUserInsightRepository
from app.infrastructure.postgres.repos.intents import PostgresUserIntentRepository


class IUnitOfWork:
    users: IUserRepository
    exercises: IExerciseRepository
    programs: IWorkoutProgramRepository
    workout_days: IWorkoutDayRepository
    workout_days_exercise: IWorkoutDayExerciseRepository
    insights: IUserInsightRepository
    intents: IUserIntentRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class PostgresUnitOfWork(IUnitOfWork):
    def __init__(self):
        self._session_factory = async_session_maker
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "PostgresUnitOfWork":
        self._session = self._session_factory()

        self.users = PostgresUserRepository(self._session)
        self.exercises = PostgresExerciseRepository(self._session)
        self.programs = PostgresWorkoutProgramRepository(self._session)
        self.workout_days = PostgresWorkoutDayRepository(self._session)
        self.workout_days_exercise = PostgresWorkoutDayExerciseRepository(self._session)
        self.insights = PostgresUserInsightRepository(self._session)
        self._intents = PostgresUserIntentRepository(self._session)

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
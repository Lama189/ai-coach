from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.training.workout_day import WorkoutDay


class IWorkoutDayRepository(ABC):

    @abstractmethod
    async def save(self, workout_day: WorkoutDay, program_id: UUID) -> None:
        ...

    
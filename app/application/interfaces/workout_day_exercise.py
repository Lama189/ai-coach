from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.training.workout_day_exercise import WorkoutDayExercise


class IWorkoutDayExerciseRepository(ABC):

    @abstractmethod
    async def save(self, workout_day_exercise: WorkoutDayExercise, workout_day_id: UUID) -> None:
        ...

    
    @abstractmethod
    async def get_by_workout_day_id(self, workout_day_id: UUID) -> list[WorkoutDayExercise]:
        ...
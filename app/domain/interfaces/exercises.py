from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.enums import MuscleGroup
from app.domain.training.exercise import Exercise


class IExerciseRepository(ABC):

    @abstractmethod
    async def save_exercise(self, exercise: Exercise) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Exercise | None:
        ...

    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        muscle_group: MuscleGroup | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Exercise]:
        ...

    @abstractmethod
    async def get_by_ids(self, exercise_ids: list[UUID]) -> list[Exercise]:
    
        ...
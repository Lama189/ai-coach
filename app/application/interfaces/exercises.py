from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.enums import MuscleGroup
from app.domain.training.exercise import Exercise


class IExerciseRepository(ABC):

    @abstractmethod
    async def save_exercise(self, exercise: Exercise, embedding: list[float] | None = None) -> None:
        ...


    @abstractmethod
    async def get_by(self, **kwargs) -> Exercise | None:
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
    async def search_relevant(
        self,
        muscle_groups: list[str],
        excluded_patterns: list[str],
        excluded_equipment: list[str],
        embedding: list[float] | None,
        limit: int,
    ) -> list[Exercise]: ...


    async def find_familiar(
        self,
        embedding: list[float],
        threshold: float = 0.85,
    ) -> Exercise | None:
        ...


    @abstractmethod
    async def get_by_ids(self, exercise_ids: list[UUID]) -> list[Exercise]:
        ...


    @abstractmethod
    async def delete(self, exercise_id: UUID) -> None:
        ...
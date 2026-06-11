from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.training.program import WorkoutProgram


class IWorkoutProgramRepository(ABC):

    @abstractmethod
    async def save(self, program: WorkoutProgram, task_id: UUID | None = None) -> None:
        ...

    @abstractmethod
    async def get_actual_by_user_id(self, user_id: UUID) -> WorkoutProgram | None:
        ...

    @abstractmethod
    async def get_by_task_id(self, task_id: UUID) -> WorkoutProgram | None:
        ...

    @abstractmethod
    async def deactivate_all_for_user(self, user_id: UUID) -> None:
        ...
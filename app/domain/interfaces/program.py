from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.training.program import WorkoutProgram


class IWorkoutProgramRepository(ABC):

    @abstractmethod
    async def save(self, program: WorkoutProgram) -> None:
        ...

    # @abstractmethod
    # async def get_by_id(self, program_id: UUID) -> WorkoutProgram | None:
    #     ...

    @abstractmethod
    async def deactivate_all_for_user(self, user_id: UUID) -> None:
        ...
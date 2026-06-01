from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.training.program import WorkoutProgram


class IWorkoutProgramRepository(ABC):

    @abstractmethod
    async def save(self, program: WorkoutProgram) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, program_id: UUID) -> WorkoutProgram | None:
        ...

    @abstractmethod
    async def get_user_programs(self, user_id: UUID, only_active: bool = False) -> list[WorkoutProgram]:
        ...

    @abstractmethod
    async def delete(self, program_id: UUID) -> None:
        ...
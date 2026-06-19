from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.identity.user_schedule import UserSchedule


class IUserScheduleRepository(ABC):

    @abstractmethod
    async def save(self, schedule: UserSchedule) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, schedule_id: UUID) -> UserSchedule | None:
        ...

    @abstractmethod
    async def delete(self, schedule_id: UUID) -> None:
        ...

    @abstractmethod
    async def search_by(
        self,
        user_id: UUID | None = None,
        day_of_week: int | None = None,
        training_day_number: int | None = None,
    ) -> list[UserSchedule]:
        ...

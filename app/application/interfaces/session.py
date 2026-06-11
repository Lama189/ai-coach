from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.training.session import WorkoutSessionDomain


class ISessionRepository(ABC):

    @abstractmethod
    async def save(self, session: WorkoutSessionDomain) -> None:
        ...

    @abstractmethod
    async def get_by(self, with_relations: bool = True, **kwargs) -> WorkoutSessionDomain | None:
        ...

    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[WorkoutSessionDomain]:
        ...

    @abstractmethod
    async def count_user_sessions(self, user_id: UUID) -> int:
        ...
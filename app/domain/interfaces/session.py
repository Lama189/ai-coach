from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.training.session import Session


class ISessionRepository(ABC):

    @abstractmethod
    async def save(self, session: Session) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Session | None:
        ...

    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Session]:
        ...

    @abstractmethod
    async def count_user_sessions(self, user_id: UUID) -> int:
        ...
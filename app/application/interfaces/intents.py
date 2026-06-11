from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.identity.intents import UserIntent


class IUserIntentRepository(ABC):

    @abstractmethod
    async def save(
        self,
        intent: UserIntent,
        embedding: list[float] | None = None,
    ) -> None: ...

    @abstractmethod
    async def find_similar(
        self,
        user_id: UUID,
        query_embedding: list[float],
        threshold: float = 0.92,
        limit: int = 1,
    ) -> UserIntent | None: ...

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
    ) -> list[UserIntent]: ...
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.identity.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def save(self, user: User) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool | None:
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        ...

    
    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        ...
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.identity.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def save(self, user: User) -> None:
        ...
        

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        ...


    @abstractmethod
    async def get_by(self, with_relations: bool = True, **kwargs) -> User | None:
        ...

    
    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        ...
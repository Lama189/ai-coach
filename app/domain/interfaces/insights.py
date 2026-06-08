from abc import abstractmethod, ABC
from uuid import UUID
from app.domain.identity.insight import UserInsight


class IUserInsightRepository(ABC):

    @abstractmethod
    async def save(self, insight: UserInsight, embedding: list[float] | None = None) -> None:
        ...

    
    @abstractmethod
    async def search_by_vector(self, user_id: UUID, query_embedding: list[float], limit: int = 3) -> list[UserInsight]:
        ...
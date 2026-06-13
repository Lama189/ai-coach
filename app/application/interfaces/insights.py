from abc import abstractmethod, ABC
from uuid import UUID

from app.domain.identity.insight import UserInsight
from app.domain.enums import InsightTag


class IUserInsightRepository(ABC):

    @abstractmethod
    async def save(self, insight: UserInsight, embedding: list[float] | None = None) -> None:
        ...

    
    @abstractmethod
    async def search_by(
        self, user_id: UUID | None, 
        query_embedding: list[float] | None = None, 
        tags: list[InsightTag] | None = None,
        limit: int = 3
    ) -> list[UserInsight]:
        ...

    @abstractmethod
    async def update(
        self,
        insight_id: UUID,
        **kwargs,
    ) -> None: ...

    @abstractmethod
    async def delete(
        self,
        insight_id: UUID,
    ) -> None: ...
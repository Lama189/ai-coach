from abc import ABC, abstractmethod

class IEmbeddingService(ABC):

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        ...
from abc import ABC, abstractmethod

class ILLMService(ABC):

    @abstractmethod
    async def generate(self, user_message: str, context_text: str) -> str:
        ...

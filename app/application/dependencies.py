from functools import lru_cache
from collections.abc import AsyncGenerator

from app.core.config import get_settings
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork, IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService


settings = get_settings()


async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow


def get_llm_api_key() -> str:
    return settings.llm_api_key


@lru_cache(maxsize=1)
def get_embedding_service() -> SentenceTransformerEmbeddingService:
    return SentenceTransformerEmbeddingService()
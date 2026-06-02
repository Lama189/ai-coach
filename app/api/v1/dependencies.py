from collections.abc import AsyncGenerator

from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork, IUnitOfWork
from app.core.config import get_settings

settings = get_settings()

async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow


async def get_llm_api_key() -> str:
    return settings.llm_api_key
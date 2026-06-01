from collections.abc import AsyncGenerator

from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork, IUnitOfWork

async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow
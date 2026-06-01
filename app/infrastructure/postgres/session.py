from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection

from app.infrastructure.postgres.database import async_session_maker, engine

async def get_async_connection() -> AsyncGenerator[AsyncConnection, None]:
    async with engine.begin() as conn:
        yield conn

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
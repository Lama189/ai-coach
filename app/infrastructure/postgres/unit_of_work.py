from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.database import async_session_maker
from app.domain.interfaces.identity import IUserRepository
from app.infrastructure.postgres.repos.identity import PostgresUserRepository


class IUnitOfWork:
    users: IUserRepository
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class PostgresUnitOfWork(IUnitOfWork):
    def __init__(self):
        self._session_factory = async_session_maker
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "PostgresUnitOfWork":
        self._session = self._session_factory()

        self.users = PostgresUserRepository(self._session)
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()
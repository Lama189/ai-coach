from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from redis.asyncio import Redis
from functools import lru_cache
from collections.abc import AsyncGenerator

from app.core.config import get_settings
from app.core.security import SecurityUtils

from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.repos.repository import RedisRepository

from app.application.services.user_service import UserService


settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow


def get_llm_api_key() -> str:
    return settings.llm_api_key


@lru_cache(maxsize=1)
def get_embedding_service() -> SentenceTransformerEmbeddingService:
    return SentenceTransformerEmbeddingService()


def get_redis_repository(
    client: Redis = Depends(get_redis_client)
)-> RedisRepository:
    return RedisRepository(client=client)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis: RedisRepository = Depends(get_redis_repository),
    uow: IUnitOfWork = Depends(get_uow)
):
    payload = SecurityUtils.verify_token(token)
    user_id = payload.get("sub")

    cached_user = await redis.get_user(user_id)
    if cached_user:
        return cached_user
    
    service = UserService(uow)
    db_user = await service.get_user(user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found"
        )
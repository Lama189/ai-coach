import logging
from redis.asyncio import Redis, RedisError

from app.core.config import get_settings
from app.application.dto.identity import UserCachedDTO


settings = get_settings()
logger = logging.getLogger(__name__)


class RedisRepository:
    def __init__(self, client: Redis) -> None:
        self._client = client

    
    async def get_refresh_token(self, user_id: str) -> str | None:
        try:
            return str(await self._client.get(f"refresh_token:{user_id}"))
        
        except RedisError as e:
            logger.error(f"Failed to get refresh_token for {user_id}: {e}")
            return None
    

    async def set_refresh_token(
        self, 
        user_id: str, 
        token: str, 
        expire_days: int = settings.refresh_token_expire_days
    ) -> None:
        try:
            await self._client.set(
                f"refresh_token:{user_id}",
                token,
                ex=expire_days * 24 * 60 * 60
            )

        except RedisError as e:
            logger.error(f"Failed to set refresh_token for {user_id}: {e}")

    
    async def delete_refresh_token(self, user_id: str) -> None:
        try:
            await self._client.delete(f"refresh_token:{user_id}")

        except RedisError as e:
            logger.error(f"Failed to delete refresh_token in Redis for {user_id}: {e}")

    
    async def set_user(self, user_id: str, user: UserCachedDTO, expire_secconds: int = 900) -> None:
        try:
            await self._client.set(f"user:{user_id}", user.model_dump_json(), ex=expire_secconds)

        except RedisError as e:
            logger.error(f"Failed to set user for {user_id}: {e}")


    async def get_user(self, user_id: str) -> UserCachedDTO | None:
        try:
            user_json = await self._client.get(f"user:{user_id}")
            if not user_json:
                return None
            
            return UserCachedDTO.model_validate_json(user_json)
        
        except RedisError as e:
            logger.error(f"Failed to get user in Redis for {user_id}: {e}")

    
    async def delete_user(self, user_id: str):
        try:
            await self._client.delete(f"user:{user_id}")
        except RedisError as e:
            logger.error(f"Failed to delete user in Redis for {user_id}: {e}")

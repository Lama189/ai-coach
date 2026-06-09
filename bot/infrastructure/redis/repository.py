from redis.asyncio import Redis, RedisError


class BotRedisRepository:
    def __init__(self, client: Redis) -> None:
        self._client = client

    
    async def set_access_token(
        self, 
        telegram_id: int, 
        token: str, 
        expire_minutes: int = 15
    ) -> None:
        try:
            await self._client.setex(
                f"bot:access_token:{telegram_id}",
                expire_minutes * 60,
                token
            )

        except RedisError as e:
            return None
        
    
    async def set_refresh_token(
        self,
        telegram_id: int,
        token: str,
        expire_days: int = 30
    ) -> None:
        try:
            await self._client.setex(
                f"bot:refresh_token:{telegram_id}",
                expire_days * 24 * 60 * 60,
                token
            )
        
        except RedisError as e:
            return None
        

    async def set_user_id(
        self, 
        telegram_id: int,
        user_id: str,
        expire_days: int = 30
    ) -> None:
        try:
            await self._client.setex(
                f"bot:user_id:{telegram_id}",
                expire_days * 24 * 60 * 60,
                user_id
            )

        except RedisError as e:
            return None
        
    
    async def get_access_token(self, telegram_id: int) -> str | None:
        token = await self._client.get(f"bot:access_token:{telegram_id}")
        return str(token) if token else None
    

    async def get_refresh_token(self, telegram_id: int) -> str | None:
        token = await self._client.get(f"bot:refresh_token:{telegram_id}")
        return str(token) if token else None
    

    async def clear_all(self, telegram_id: int) -> None:
        await self._client.delete(
            f"bot:access_token:{telegram_id}",
            f"bot:refresh_token:{telegram_id}",
            f"bot:user_id:{telegram_id}",
        )
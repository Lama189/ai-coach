import httpx

from bot.infrastructure.redis.repository import BotRedisRepository

class APIClient:
    def __init__(self, base_url: str, redis: BotRedisRepository) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=5.0,
                read=30.0,
                write=5.0,
                pool=5.0
            ),
        )
        self._redis = redis

    
    async def _request_with_retry(
        self, 
        method: str,
        url: str,
        retries: int = 3,
        **kwargs
    ) -> httpx.Response:
        if retries <= 0:
            raise ValueError("Количество попыток (retries) должно быть больше 0")

        for attempt in range(retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code not in (500, 502):
                    raise
                
                if attempt == retries - 1:
                    raise

        raise RuntimeError("Цикл повторных попыток завершился неожиданно")
    

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        try:
            response = await self._request_with_retry(
                "GET",
                f"/api/v1/users/telegram/{telegram_id}"
            )
            return response.json()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    
    async def check_phone(self, phone: str) -> bool:
        try:
            response = await self._request_with_retry(
                "GET",
                f"/api/v1/users/exists/phone/{phone}"
            )
            return bool(response.json())
        
        except httpx.HTTPStatusError as e:
            raise e
        
    
    async def register_user(self, user_data: dict) -> dict:
        try:
            response = await self._request_with_retry(
                "POST",
                f"/api/v1/users/register",
                json=user_data
            )
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise e
        

    async def login(self, user_data: dict) -> dict:
        try:
            response = await self._request_with_retry(
                "POST",
                f"/api/v1/users/login",
                json=user_data
            )
        
        except httpx.HTTPStatusError as e:
            raise e
        
        response.raise_for_status()
        response_data = response.json()

        await self._redis.set_access_token(user_data["telegram_id"], response_data["access_token"])
        await self._redis.set_refresh_token(user_data["telegram_id"], response_data["refresh_token"])
        await self._redis.set_user_id(user_data["telegram_id"], str(response_data["user_id"]))

        return response_data


    async def _refresh_access_token(self, telegram_id: int) -> str | None:
        refresh_token = await self._redis.get_refresh_token(telegram_id)
        if not refresh_token:
            return None

        try:
            response = await self._client.post(
                "/api/v1/users/refresh",
                json={"refresh_token": refresh_token},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return None

        data = response.json()
        await self._redis.set_access_token(telegram_id, data["access_token"])
        await self._redis.set_refresh_token(telegram_id, data["refresh_token"])
        return data["access_token"]


    async def create_insight(
        self, telegram_id: int, tag: str, content: str
    ) -> dict:
        token = await self._redis.get_access_token(telegram_id)
        if not token:
            raise ValueError("Токен доступа не найден. Выполните /auth")

        try:
            response = await self._request_with_retry(
                "POST",
                "/api/v1/insights/",
                json={"tag": tag, "content": content},
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code != 401:
                raise

            new_token = await self._refresh_access_token(telegram_id)
            if not new_token:
                raise ValueError("Сессия истекла. Выполните /auth")

            try:
                response = await self._request_with_retry(
                    "POST",
                    "/api/v1/insights/",
                    json={"tag": tag, "content": content},
                    headers={"Authorization": f"Bearer {new_token}"},
                )
                return response.json()
            except httpx.HTTPStatusError:
                raise ValueError("Не удалось создать инсайт после обновления токена")


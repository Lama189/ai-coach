import httpx


class APIClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=5.0,
                read=30.0,
                write=5.0,
                pool=5.0
            ),
        )

    
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
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.api.client import APIClient


class APIClientMiddleware(BaseMiddleware):
    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    
    async def __call__(
        self, 
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], 
        event: TelegramObject, 
        data: dict[str, Any],
    ) -> Any:
        data["api_client"] = self._api_client
        return await handler(event, data)

        
        
import asyncio
from aiogram import Bot, Dispatcher

from bot.core.config import get_settings
from bot.api.client import APIClient
from bot.middlewares.api_client import APIClientMiddleware

from bot.routers.start import router as start_router
from bot.routers.auth import router as auth_router


async def main():
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    api_client = APIClient(base_url="http://fitness_api:8000")

    dp.message.middleware(APIClientMiddleware(api_client=api_client))
    dp.callback_query.middleware(APIClientMiddleware(api_client=api_client))

    dp.include_router(start_router)
    dp.include_router(auth_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
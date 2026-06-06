import asyncio
from aiogram import Bot, Dispatcher

from bot.core.config import get_settings
from bot.routers.start import router as start_router

settings = get_settings()
bot = Bot(token=settings.bot_token)
dp = Dispatcher()


dp.include_router(start_router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
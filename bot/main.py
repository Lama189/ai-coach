import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.core.config import get_settings
from bot.api.client import APIClient
from bot.middlewares.api_client import APIClientMiddleware
from bot.infrastructure.redis.repository import BotRedisRepository

from bot.routers.start import router as start_router
from bot.routers.auth import router as auth_router
from bot.routers.insight import router as insight_router


settings = get_settings()


async def on_startup(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)


async def on_shutdown(bot: Bot, redis: Redis) -> None:
    await redis.aclose()


async def main():
    redis = Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, decode_responses=True)
    redis_repo = BotRedisRepository(redis)

    try:
        await redis.ping()
        print("Redis бота подключён — база /1")
    except Exception as e:
        raise RuntimeError(f"Redis недоступен: {e}")

    storage = RedisStorage(redis=redis)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    api_client = APIClient(base_url=settings.api_base_url, redis=redis_repo)

    dp.message.middleware(APIClientMiddleware(api_client=api_client))
    dp.callback_query.middleware(APIClientMiddleware(api_client=api_client))

    dp.include_router(start_router)
    dp.include_router(auth_router)
    dp.include_router(insight_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
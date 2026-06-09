from bot.api.client import APIClient


async def get_user_by_telegram_id(
    telegram_id: int,
    api_client: APIClient,
) -> dict | None:
    return await api_client.get_user_by_telegram_id(telegram_id)


async def is_phone_taken(
    phone: str,
    api_client: APIClient,
) -> bool:
    return await api_client.check_phone(phone)


async def register_user(
    telegram_id: int,
    phone: str,
    full_name: str,
    password: str,
    api_client: APIClient,
) -> dict:
    return await api_client.register_user({
        "telegram_id": telegram_id,
        "phone": phone,
        "username": full_name,
        "password": password,
    })


async def login_user(
    telegram_id: int,
    phone: str,
    password: str,
    api_client: APIClient,
) -> dict:
    return await api_client.login({
        "phone": phone,
        "password": password,
        "telegram_id": telegram_id,
    })
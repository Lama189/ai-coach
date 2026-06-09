import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api.client import APIClient
from bot.keyboards.auth import get_phone_keyboard, remove_keyboard
from bot.states.auth import AuthStates
from bot.usecases.auth import login_user, register_user
from bot.utils.phone import normalize_phone

router = Router(name="auth-router")


@router.message(Command("auth"))
async def auth_handler(message: Message, state: FSMContext):
    await state.clear()

    if message.from_user is None:
        return

    await message.answer(
        f"Привет, {message.from_user.first_name}! "
        "Поделись номером телефона:",
        reply_markup=get_phone_keyboard(),
    )
    await state.set_state(AuthStates.entering_phone)


@router.message(AuthStates.entering_phone, F.contact)
async def handle_phone(message: Message, state: FSMContext):
    if message.contact is None:
        return

    phone = normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer("❌ Неверный формат номера. Попробуй снова.")
        return

    await state.update_data(phone=phone)
    await message.answer(
        "Введи пароль:",
        reply_markup=remove_keyboard(),
    )
    await state.set_state(AuthStates.entering_password)


@router.message(AuthStates.entering_phone, F.text)
async def handle_phone_wrong(message: Message):
    await message.answer(
        "Используй кнопку для отправки номера.",
        reply_markup=get_phone_keyboard(),
    )


@router.message(AuthStates.entering_password, F.text)
async def handle_password(
    message: Message,
    state: FSMContext,
    api_client: APIClient,
):
    if message.text is None or message.from_user is None:
        return

    data = await state.get_data()
    password = message.text.strip()

    if len(password) < 8:
        await message.answer("Пароль должен быть не менее 8 символов:")
        return

    try:
        await login_user(
            telegram_id=message.from_user.id,
            phone=data["phone"],
            password=password,
            api_client=api_client,
        )
        await state.clear()
        await message.answer("Вход выполнен ✅")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            await message.answer(
                "❌ Неверный пароль. Попробуй снова:"
            )
        
        elif e.response.status_code == 404:
            await state.update_data(password=password)
            await message.answer(
                "Аккаунта с таким номером нет.\n\n"
                "Введи своё полное ФИО для регистрации:"
            )
            await state.set_state(AuthStates.entering_full_name)

        else:
            await message.answer("Что-то пошло не так. Попробуй позже.")
            await state.clear()


@router.message(AuthStates.entering_full_name, F.text)
async def handle_full_name(
    message: Message,
    state: FSMContext,
    api_client: APIClient,
):
    if message.text is None or message.from_user is None:
        return

    full_name = message.text.strip()

    if len(full_name.split()) < 2:
        await message.answer("Введи полное ФИО, например: Иванов Иван Иванович")
        return

    data = await state.get_data()

    try:
        await register_user(
            telegram_id=message.from_user.id,
            phone=data["phone"],
            full_name=full_name,
            password=data["password"],
            api_client=api_client,
        )
        await state.clear()
        await message.answer(
            "Регистрация завершена! 🎉\n\n"
            "Заполни профиль чтобы получить персональную программу тренировок."
        )

    except httpx.HTTPStatusError:
        await message.answer("Что-то пошло не так. Попробуй ещё раз через /auth")
        await state.clear()
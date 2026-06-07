from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api.client import APIClient
from bot.keyboards.auth import get_phone_keyboard, remove_keyboard
from bot.states.auth import OnboardingStates
from bot.usecases.auth import get_user_by_telegram_id, is_phone_taken, register_user
from bot.utils.phone import normalize_phone

router = Router(name="auth-router")


@router.message(Command("auth"))
async def auth_handler(message: Message, state: FSMContext, api_client: APIClient):
    await state.clear()

    if message.from_user is None:
        return

    user = await get_user_by_telegram_id(
        telegram_id=message.from_user.id,
        api_client=api_client,
    )

    if user is not None:
        await message.answer(
            f"С возвращением, {message.from_user.full_name}! "
            "Тебе не нужно проходить регистрацию."
        )
        await state.clear()
        return

    await message.answer(
        f"Добро пожаловать, {message.from_user.full_name}! "
        "Я твой личный ИИ-тренер.\n\n"
        "Поделись номером телефона для регистрации:",
        reply_markup=get_phone_keyboard(),
    )
    await state.set_state(OnboardingStates.entering_phone)


@router.message(OnboardingStates.entering_phone, F.contact)
async def handle_phone_contact(
    message: Message,
    state: FSMContext,
    api_client: APIClient,
):
    if message.contact is None or message.from_user is None:
        await message.answer("Пожалуйста, поделись номером через кнопку.")
        return

    phone = normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer("❌ Неверный формат номера. Попробуй снова.")
        return

    taken = await is_phone_taken(phone=phone, api_client=api_client)
    if taken:
        await message.answer(
            "Этот номер уже зарегистрирован. Попробуй другой.",
            reply_markup=get_phone_keyboard(),
        )
        return

    await state.update_data(phone=phone)
    await message.answer(
        "Номер принят ✅\n\nТеперь введи своё полное ФИО:",
        reply_markup=remove_keyboard(),
    )
    await state.set_state(OnboardingStates.entering_full_name)


@router.message(OnboardingStates.entering_phone, F.text)
async def handle_phone_wrong_format(message: Message):
    await message.answer(
        "Пожалуйста, используй кнопку ниже чтобы поделиться номером.",
        reply_markup=get_phone_keyboard(),
    )


@router.message(OnboardingStates.entering_full_name, F.text)
async def handle_full_name(message: Message, state: FSMContext):
    if message.text is None:
        return

    full_name = message.text.strip()

    if len(full_name.split()) < 2:
        await message.answer("Введи полное ФИО, например: Иванов Иван Иванович")
        return

    await state.update_data(full_name=full_name)
    await message.answer(
        f"Отлично, {full_name.split()[1]}! "
        "Теперь придумай пароль (минимум 8 символов):"
    )
    await state.set_state(OnboardingStates.entering_password)


@router.message(OnboardingStates.entering_password, F.text)
async def finish_registration(
    message: Message,
    state: FSMContext,
    api_client: APIClient,
):
    if message.text is None or message.from_user is None:
        return

    password = message.text.strip()

    if len(password) < 8:
        await message.answer("Пароль должен быть не менее 8 символов. Попробуй снова:")
        return

    data = await state.get_data()

    try:
        await register_user(
            telegram_id=message.from_user.id,
            phone=data["phone"],
            full_name=data["full_name"],
            password=password,
            api_client=api_client,
        )
    except Exception:
        await message.answer("Что-то пошло не так. Попробуй ещё раз через /auth")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        "Регистрация завершена! 🎉\n\n"
        "Чтобы пользоваться ai-генерациями в будущем, заполни свой профиль в разделе настроек",
    )
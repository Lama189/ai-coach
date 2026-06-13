from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api.client import APIClient
from bot.keyboards.insight import (
    InsightTag,
    INSIGHT_TAG_LABELS,
    get_insight_tag_keyboard,
)
from bot.states.insight import InsightStates
from bot.keyboards.auth import remove_keyboard

router = Router(name="insight-router")

_LABEL_TO_TAG: dict[str, InsightTag] = {v: k for k, v in INSIGHT_TAG_LABELS.items()}


@router.message(Command("insight"))
async def cmd_insight(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите тип инсайта:",
        reply_markup=get_insight_tag_keyboard(),
    )
    
    await state.set_state(InsightStates.choosing_tag)


@router.message(InsightStates.choosing_tag, F.text)
async def handle_tag_choice(message: Message, state: FSMContext):
    if message.text is None:
        return

    tag = _LABEL_TO_TAG.get(message.text)
    if tag is None:
        await message.answer("Выберите тег из предложенных вариантов:")
        return

    await state.update_data(tag=tag.value)
    await message.answer(
        "Введите текст инсайта:",
        reply_markup=remove_keyboard(),
    )
    await state.set_state(InsightStates.entering_text)


@router.message(InsightStates.entering_text, F.text)
async def handle_insight_text(
    message: Message,
    state: FSMContext,
    api_client: APIClient,
):
    if message.text is None or message.from_user is None:
        return

    data = await state.get_data()
    tag = data["tag"]
    content = message.text.strip()

    if not content:
        await message.answer("Текст не может быть пустым. Введите инсайт:")
        return

    try:
        await api_client.create_insight(
            telegram_id=message.from_user.id,
            tag=tag,
            content=content,
        )
        await state.clear()
        await message.answer("Инсайт сохранён ✅")
    except ValueError as e:
        await message.answer(str(e))
        await state.clear()
    except Exception:
        await message.answer("Не удалось сохранить инсайт. Попробуйте позже.")
        await state.clear()

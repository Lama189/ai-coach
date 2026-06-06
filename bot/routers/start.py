from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from bot.usecases.start import start_usecase


router = Router(name="start-router")


@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()

    await start_usecase(message)
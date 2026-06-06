from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext


async def start_usecase(message: types.Message):
    await message.answer("Приветствую. Я твой личный ИИ-тренер. С чего начнём?")
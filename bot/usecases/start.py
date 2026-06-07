from aiogram import types


async def start_usecase(message: types.Message):
    await message.answer("Приветствую. Я твой личный ИИ-тренер. С чего начнём?")
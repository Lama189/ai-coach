from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    entering_phone    = State()
    entering_password = State()
    entering_full_name = State()
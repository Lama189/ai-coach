from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    entering_full_name = State()
    entering_phone     = State()
    entering_password  = State()
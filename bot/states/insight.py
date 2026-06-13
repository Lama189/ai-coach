from aiogram.fsm.state import State, StatesGroup


class InsightStates(StatesGroup):
    choosing_tag   = State()
    entering_text  = State()

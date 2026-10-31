from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    bankroll = State()


class InsightStates(StatesGroup):
    waiting_text = State()


class SeoStates(StatesGroup):
    waiting_query = State()


class HrStates(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class HoroscopeStates(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_time_known = State()
    waiting_for_birth_time = State()
    waiting_for_birth_place = State()
    waiting_for_gender = State()
    waiting_for_focus = State()
    waiting_for_regeneration = State()

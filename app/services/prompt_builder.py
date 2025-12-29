from __future__ import annotations

from dataclasses import dataclass

from app.modules.horoscope.prompts import HOROSCOPE_TEMPLATE


@dataclass
class HoroscopeRequest:
    mode: str
    birth_date: str
    birth_time: str | None
    birth_place: str
    gender: str
    focus: str


FOCUS_LABELS = {
    "focus_love": "любовь",
    "focus_money": "финансы",
    "focus_health": "здоровье",
    "focus_career": "карьера",
    "focus_general": "общее",
}

GENDER_LABELS = {
    "gender_m": "мужской",
    "gender_f": "женский",
    "gender_o": "другое",
}


def build_horoscope_prompt(req: HoroscopeRequest) -> str:
    focus = FOCUS_LABELS.get(req.focus, "общее")
    gender = GENDER_LABELS.get(req.gender, "")
    time_info = req.birth_time if req.birth_time else "неизвестно"
    return HOROSCOPE_TEMPLATE.format(
        mode=req.mode,
        birth_date=req.birth_date,
        birth_time=time_info,
        birth_place=req.birth_place,
        gender=gender,
        focus=focus,
    )

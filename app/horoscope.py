"""Prompt builder and zodiac data."""
from __future__ import annotations

SIGNS = [
    "Овен",
    "Телец",
    "Близнецы",
    "Рак",
    "Лев",
    "Дева",
    "Весы",
    "Скорпион",
    "Стрелец",
    "Козерог",
    "Водолей",
    "Рыбы",
]

PERIODS = {
    "today": "сегодня",
    "week": "на неделю",
}


def build_prompt(sign: str, period_key: str) -> str:
    period = PERIODS.get(period_key, period_key)
    return (
        "Сделай короткий, дружелюбный и вдохновляющий гороскоп для знака "
        f"{sign} {period}. Используй понятный язык и избегай банальностей."
    )


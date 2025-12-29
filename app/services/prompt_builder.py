from __future__ import annotations

from dataclasses import dataclass

from app.config.runtime import runtime_config
from app.modules.horoscope.prompts import HOROSCOPE_TEMPLATE


@dataclass(slots=True)
class HoroscopeRequest:
    mode: str
    birth_date: str
    birth_time: str | None
    birth_place: str
    gender: str
    focus: str


@dataclass(slots=True)
class BuiltPrompt:
    system_prompt: str
    user_prompt: str


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


def build_horoscope_prompt(req: HoroscopeRequest) -> BuiltPrompt:
    focus = FOCUS_LABELS.get(req.focus, "общее")
    gender = GENDER_LABELS.get(req.gender, "")
    time_info = req.birth_time if req.birth_time else "неизвестно"

    style = runtime_config.prompt_style
    tone = style.get("tone")
    bullets = style.get("bullets_count") or style.get("bullets") or 6

    system_prompt = (
        "Ты опытный астролог и психолог. Отвечай по-русски, вежливо и без шарлатанства. "
        "Не давай медицинских диагнозов, избегай упоминаний о магии и эзотерике. "
        "Формат ответа — структурированный список из 6-10 пунктов с короткими заголовками: "
        "Любовь, Финансы, Здоровье, Карьера, Совет дня."
    )
    if tone:
        system_prompt = f"{system_prompt} Тон: {tone}."

    user_prompt = HOROSCOPE_TEMPLATE.format(
        mode=req.mode,
        birth_date=req.birth_date,
        birth_time=time_info,
        birth_place=req.birth_place,
        gender=gender,
        focus=focus,
    )
    user_prompt = (
        f"{user_prompt} Сформируй список из {bullets} пунктов (не менее 6 и не более 10). "
        "Каждый пункт начинай с названия блока и эмодзи: "
        "• Любовь: …; • Финансы: …; • Здоровье: …; • Карьера: …; • Совет дня: … "
        "Делай выводы и рекомендации, избегай общих фраз."
    )

    return BuiltPrompt(system_prompt=system_prompt, user_prompt=user_prompt)

from __future__ import annotations

HOROSCOPE_SUBTYPES = {
    "today": "☀️ Сегодня",
    "tomorrow": "🌙 Завтра",
    "week": "📅 Неделя",
    "month": "🧭 Месяц",
    "personal": "✨ Персональный",
}


INPUTS = {
    "birth_date": "Введите дату рождения в формате ДД.ММ.ГГГГ",
    "birth_time": "Введите время рождения (опционально, можно пропустить)",
    "birth_place": "Введите город рождения",
    "current_city": "Введите текущий город (опционально)",
    "focus": "Выберите фокус: любовь/деньги/здоровье/работа/общее",
}


def build_preview(flow: dict) -> str:
    subtype = flow.get("subtype")
    inputs = flow.get("inputs", {})
    lines = [f"Тип: {HOROSCOPE_SUBTYPES.get(subtype, subtype)}"]
    for key in ["birth_date", "birth_time", "birth_place", "current_city", "focus"]:
        if inputs.get(key):
            lines.append(f"{key}: {inputs.get(key)}")
    return "\n".join(lines)


def build_ai_payload(flow: dict) -> dict:
    return {
        "module": "horoscope",
        "subtype": flow.get("subtype"),
        "inputs": flow.get("inputs", {}),
    }

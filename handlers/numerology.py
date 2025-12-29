from __future__ import annotations

NUMEROLOGY_SUBTYPES = {
    "destiny": "🔢 Число судьбы",
    "day": "📅 Число дня",
    "karma": "🧬 Кармические задачи",
    "personality": "🧠 Личностный код",
}


INPUTS = {
    "birth_date": "Введите дату рождения (ДД.ММ.ГГГГ)",
    "name": "Имя/ФИО (опционально)",
    "goal": "Цель дня или запроса (опционально)",
}


def build_preview(flow: dict) -> str:
    subtype = flow.get("subtype")
    inputs = flow.get("inputs", {})
    lines = [f"Тип: {NUMEROLOGY_SUBTYPES.get(subtype, subtype)}"]
    for key in ["birth_date", "name", "goal"]:
        if inputs.get(key):
            lines.append(f"{key}: {inputs[key]}")
    return "\n".join(lines)


def build_ai_payload(flow: dict) -> dict:
    return {
        "module": "numerology",
        "subtype": flow.get("subtype"),
        "inputs": flow.get("inputs", {}),
    }

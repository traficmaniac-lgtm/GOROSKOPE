from __future__ import annotations

COMPAT_SUBTYPES = {
    "love": "💞 Любовь",
    "friend": "🤝 Дружба",
    "business": "💼 Бизнес",
    "full": "⭐ Полный отчёт",
}


def build_preview(flow: dict) -> str:
    inputs = flow.get("inputs", {})
    subtype = flow.get("subtype")
    lines = [f"Формат: {COMPAT_SUBTYPES.get(subtype, subtype)}"]
    for who in ("person_1", "person_2"):
        data = inputs.get(who, {})
        if data:
            lines.append(f"{who}: {data.get('name','?')} / {data.get('birth_date','?')}")
    if subtype == "business" and inputs.get("interaction"):
        lines.append(f"Тип взаимодействия: {inputs['interaction']}")
    return "\n".join(lines)


def build_ai_payload(flow: dict) -> dict:
    return {
        "module": "compat",
        "subtype": flow.get("subtype"),
        "inputs": flow.get("inputs", {}),
    }

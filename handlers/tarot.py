from __future__ import annotations

import random

TAROT_SUBTYPES = {
    "one_card": "🔮 Одна карта",
    "three_cards": "🃏 Три карты",
    "yes_no": "🕯️ Да/Нет",
    "love": "💞 Отношения",
    "career": "💼 Работа и деньги",
    "deep": "⭐ Глубокий расклад",
}

CARD_DECK = [
    "Шут",
    "Маг",
    "Жрица",
    "Императрица",
    "Император",
    "Иерофант",
    "Влюблённые",
    "Колесница",
    "Сила",
    "Отшельник",
    "Колесо Фортуны",
    "Справедливость",
    "Повешенный",
    "Смерть",
    "Умеренность",
    "Дьявол",
    "Башня",
    "Звезда",
    "Луна",
    "Солнце",
    "Суд",
    "Мир",
]


def draw_cards(count: int) -> list[str]:
    deck = CARD_DECK.copy()
    random.shuffle(deck)
    return deck[:count]


def build_preview(flow: dict) -> str:
    subtype = flow.get("subtype")
    inputs = flow.get("inputs", {})
    lines = [f"Расклад: {TAROT_SUBTYPES.get(subtype, subtype)}"]
    lines.append(f"Вопрос: {inputs.get('question', '—')}")
    if inputs.get("context"):
        lines.append(f"Контекст: {inputs['context']}")
    if cards := inputs.get("cards"):
        lines.append("Карты: " + ", ".join(cards))
    return "\n".join(lines)


def build_ai_payload(flow: dict) -> dict:
    return {
        "module": "tarot",
        "subtype": flow.get("subtype"),
        "inputs": flow.get("inputs", {}),
    }

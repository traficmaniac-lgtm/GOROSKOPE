from __future__ import annotations

from typing import Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

from handlers import shared

SUBSERVICE, ZODIAC, TONE, NATAL_DATE, NATAL_TIME_CHOICE, NATAL_TIME_VALUE, NATAL_PLACE, CONFIRM = range(8)

HORO_SUBSERVICES: List[tuple[str, str]] = [
    ("Ежедневный", "daily"),
    ("Недельный", "week"),
    ("Месячный", "month"),
    ("Натальная карта", "natal"),
]

ZODIAC_SIGNS = [
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


def _home_button() -> List[List[InlineKeyboardButton]]:
    return [[InlineKeyboardButton("🏠 Домой", callback_data="nav:home")]]


def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        context.user_data.pop("horoscope", None)
        await query.answer()
        await query.edit_message_text(
            "✨ Гороскоп: выбери формат",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text, callback_data=f"horoscope:sub:{code}")] for text, code in HORO_SUBSERVICES]
                + [[InlineKeyboardButton("📜 История", callback_data="history:open")]]
                + _home_button()
            ),
        )
    else:
        await update.effective_message.reply_text(
            "✨ Гороскоп: выбери формат",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text, callback_data=f"horoscope:sub:{code}")] for text, code in HORO_SUBSERVICES]
                + [[InlineKeyboardButton("📜 История", callback_data="history:open")]]
                + _home_button()
            ),
        )
    return SUBSERVICE


def choose_subservice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    subtype = query.data.split(":")[-1]
    context.user_data["horoscope"] = {"subtype": subtype, "input": {}, "style": "short"}
    if subtype == "natal":
        await query.edit_message_text("Дата рождения? (ДД.ММ.ГГГГ)", reply_markup=InlineKeyboardMarkup(_home_button()))
        return NATAL_DATE
    buttons = [[InlineKeyboardButton(sign, callback_data=f"horoscope:zodiac:{sign}")] for sign in ZODIAC_SIGNS]
    buttons += _home_button()
    await query.edit_message_text("Выбери знак", reply_markup=InlineKeyboardMarkup(buttons))
    return ZODIAC


def set_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    sign = query.data.split(":")[-1]
    context.user_data.setdefault("horoscope", {}).setdefault("input", {})["zodiac"] = sign
    tone_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("кратко", callback_data="horoscope:tone:short")],
            [InlineKeyboardButton("подробно", callback_data="horoscope:tone:full")],
        ]
        + _home_button()
    )
    await query.edit_message_text("Стиль ответа?", reply_markup=tone_buttons)
    return TONE


def set_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    style = query.data.split(":")[-1]
    context.user_data.setdefault("horoscope", {})["style"] = style
    return show_confirm(update, context)


def set_natal_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("horoscope", {}).setdefault("input", {})["birth_date"] = update.effective_message.text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("точное", callback_data="horoscope:time:exact")],
            [InlineKeyboardButton("не знаю", callback_data="horoscope:time:unknown")],
            [InlineKeyboardButton("примерно", callback_data="horoscope:time:approx")],
        ]
        + _home_button()
    )
    await update.effective_message.reply_text("Время рождения?", reply_markup=kb)
    return NATAL_TIME_CHOICE


def set_natal_time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    choice = query.data.split(":")[-1]
    context.user_data.setdefault("horoscope", {}).setdefault("input", {})["birth_time"] = choice
    if choice == "unknown":
        await query.edit_message_text("Город рождения?", reply_markup=InlineKeyboardMarkup(_home_button()))
        return NATAL_PLACE
    await query.edit_message_text("Укажи время рождения текстом", reply_markup=InlineKeyboardMarkup(_home_button()))
    return NATAL_TIME_VALUE


def set_natal_time_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("horoscope", {}).setdefault("input", {})["birth_time"] = update.effective_message.text
    await update.effective_message.reply_text("Город рождения?", reply_markup=InlineKeyboardMarkup(_home_button()))
    return NATAL_PLACE


def set_natal_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("horoscope", {}).setdefault("input", {})["birth_place"] = update.effective_message.text
    return show_confirm(update, context)


def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data: Dict = context.user_data.get("horoscope", {})
    input_block = data.get("input", {})
    summary = ["✅ Проверим данные:", f"Тип: {data.get('subtype')}"]
    if "zodiac" in input_block:
        summary.append(f"Знак: {input_block['zodiac']}")
    if "birth_date" in input_block:
        summary.append(f"Дата: {input_block['birth_date']}")
    if "birth_time" in input_block:
        summary.append(f"Время: {input_block['birth_time']}")
    if "birth_place" in input_block:
        summary.append(f"Город: {input_block['birth_place']}")
    summary.append(f"Стиль: {data.get('style', 'short')}")
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Запросить прогноз", callback_data="horoscope:submit:go")],
            [InlineKeyboardButton("🔁 Ещё", callback_data="main:horoscope")],
            [InlineKeyboardButton("📜 История", callback_data="history:open")],
        ]
        + _home_button()
    )
    if update.callback_query:
        await update.callback_query.edit_message_text("\n".join(summary), reply_markup=buttons)
    else:
        await update.effective_message.reply_text("\n".join(summary), reply_markup=buttons)
    return CONFIRM


def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    data = context.user_data.get("horoscope", {})
    payload = {
        "user_id": update.effective_user.id,
        "mode": "horoscope",
        "subtype": data.get("subtype"),
        "input": data.get("input", {}),
        "style": data.get("style", "short"),
        "locale": "ru",
    }
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Ещё", callback_data="main:horoscope")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
            [InlineKeyboardButton("📜 История", callback_data="history:open")],
        ]
    )
    await shared.ensure_access_or_paywall(update, context, payload, buttons)
    return ConversationHandler.END


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start, pattern=r"^main:horoscope$")],
        states={
            SUBSERVICE: [CallbackQueryHandler(choose_subservice, pattern=r"^horoscope:sub:")],
            ZODIAC: [CallbackQueryHandler(set_zodiac, pattern=r"^horoscope:zodiac:")],
            TONE: [CallbackQueryHandler(set_tone, pattern=r"^horoscope:tone:")],
            NATAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_natal_date)],
            NATAL_TIME_CHOICE: [CallbackQueryHandler(set_natal_time_choice, pattern=r"^horoscope:time:")],
            NATAL_TIME_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_natal_time_value)],
            NATAL_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_natal_place)],
            CONFIRM: [CallbackQueryHandler(run_forecast, pattern=r"^horoscope:submit:go$")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern=r"^main:horoscope$"), CallbackQueryHandler(start, pattern=r"^nav:home$")],
        map_to_parent={ConversationHandler.END: ConversationHandler.END},
        allow_reentry=True,
        per_message=True,
    )

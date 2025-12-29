from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

from handlers import shared

SUBTYPE, BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE, STYLE, CONFIRM = range(6)


HORO_SUBTYPES = [
    ("☀️ Натальная карта", "natal"),
    ("📅 Прогноз на день", "day"),
    ("🗓 Прогноз на неделю", "week"),
    ("🌙 Лунный", "moon"),
    ("💼 Финансы/карьера", "finance"),
    ("❤️ Любовь", "love"),
]


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    buttons = [[InlineKeyboardButton(text, callback_data=f"horo:sub:{code}")] for text, code in HORO_SUBTYPES]
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="nav:home")])
    await update.effective_message.reply_text("✨ Гороскоп", reply_markup=InlineKeyboardMarkup(buttons))
    return SUBTYPE


async def choose_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    subtype = update.callback_query.data.split(":")[-1]
    context.user_data["horo"] = {"subtype": subtype, "input": {}, "style": "short"}
    await update.callback_query.edit_message_text("Дата рождения? (ДД.ММ.ГГГГ)", reply_markup=_back_keyboard())
    return BIRTH_DATE


async def set_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text
    context.user_data.setdefault("horo", {}).setdefault("input", {})["birth_date"] = text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("точное", callback_data="horo:time:exact")],
            [InlineKeyboardButton("не знаю", callback_data="horo:time:unknown")],
            [InlineKeyboardButton("примерно", callback_data="horo:time:approx")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Время рождения?", reply_markup=kb)
    return BIRTH_TIME


async def set_birth_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    value = update.callback_query.data.split(":")[-1]
    context.user_data.setdefault("horo", {}).setdefault("input", {})["birth_time"] = value
    await update.callback_query.edit_message_text("Город рождения?", reply_markup=_back_keyboard())
    return BIRTH_PLACE


async def set_birth_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("horo", {}).setdefault("input", {})["birth_place"] = update.effective_message.text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("коротко", callback_data="horo:style:short")],
            [InlineKeyboardButton("подробно", callback_data="horo:style:full")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Стиль ответа?", reply_markup=kb)
    return STYLE


async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("horo", {})["style"] = update.callback_query.data.split(":")[-1]
    return await show_confirm(update, context)


async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("horo", {})
    input_block = data.get("input", {})
    summary = (
        "✅ Проверим данные:\n"
        f"Тип: {data.get('subtype')}\n"
        f"Дата: {input_block.get('birth_date')}\n"
        f"Время: {input_block.get('birth_time')}\n"
        f"Город: {input_block.get('birth_place')}\n"
        f"Стиль: {data.get('style')}"
    )
    buttons = [
        [InlineKeyboardButton("✅ Рассчитать", callback_data="horo:go")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="main:horoscope")],
        [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
    ]
    await update.effective_message.reply_text(summary, reply_markup=InlineKeyboardMarkup(buttons))
    return CONFIRM


async def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    data = context.user_data.get("horo", {})
    payload = {
        "user_id": update.effective_user.id,
        "mode": "horoscope",
        "subtype": data.get("subtype"),
        "input": data.get("input", {}),
        "style": data.get("style", "short"),
        "locale": "ru",
        "timezone": "Europe/Kyiv",
    }
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💾 Сохранить", callback_data="history:open")],
            [InlineKeyboardButton("🔁 Уточнить", callback_data="main:horoscope")],
            [InlineKeyboardButton("🎯 Короче/подробнее", callback_data="main:horoscope")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await shared.ensure_access_or_paywall(update, context, payload, buttons)
    return ConversationHandler.END


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start, pattern=r"^main:horoscope$")],
        states={
            SUBTYPE: [CallbackQueryHandler(choose_subtype, pattern=r"^horo:sub:")],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birth_date)],
            BIRTH_TIME: [CallbackQueryHandler(set_birth_time, pattern=r"^horo:time:")],
            BIRTH_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birth_place)],
            STYLE: [CallbackQueryHandler(set_style, pattern=r"^horo:style:")],
            CONFIRM: [CallbackQueryHandler(run_forecast, pattern=r"^horo:go")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern=r"^main:horoscope$")],
        map_to_parent={ConversationHandler.END: ConversationHandler.END},
        allow_reentry=True,
    )


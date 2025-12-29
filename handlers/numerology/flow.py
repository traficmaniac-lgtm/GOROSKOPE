from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

from handlers import shared

SUBTYPE, BIRTH_DATE, NAME, STYLE, CONFIRM = range(5)

NUM_TYPES = [
    ("Число пути", "life_path"),
    ("Число имени", "destiny"),
    ("Персональный год/месяц/день", "personal"),
    ("Матрица", "matrix"),
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    buttons = [[InlineKeyboardButton(text, callback_data=f"num:sub:{code}")] for text, code in NUM_TYPES]
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="nav:home")])
    await update.effective_message.reply_text("✨ Нумерология", reply_markup=InlineKeyboardMarkup(buttons))
    return SUBTYPE


async def choose_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data["num"] = {"subtype": update.callback_query.data.split(":")[-1], "input": {}, "style": "short"}
    await update.callback_query.edit_message_text("Дата рождения?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return BIRTH_DATE


async def set_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("num", {}).setdefault("input", {})["birth_date"] = update.effective_message.text
    await update.effective_message.reply_text("Имя (если нужно) или нажми Далее", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="num:name:skip")], [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")]]))
    return NAME


async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("num", {}).setdefault("input", {})["name"] = update.effective_message.text
    return await choose_style(update, context)


async def skip_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    return await choose_style(update, context)


async def choose_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("коротко", callback_data="num:style:short")],
            [InlineKeyboardButton("подробно", callback_data="num:style:full")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Стиль?", reply_markup=kb)
    return STYLE


async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("num", {})["style"] = update.callback_query.data.split(":")[-1]
    return await show_confirm(update, context)


async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("num", {})
    summary = (
        "✅ Подтверди:\n"
        f"Тип: {data.get('subtype')}\n"
        f"Дата: {data.get('input', {}).get('birth_date')}\n"
        f"Имя: {data.get('input', {}).get('name', '—')}\n"
        f"Стиль: {data.get('style')}"
    )
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Рассчитать", callback_data="num:go")],
            [InlineKeyboardButton("✏️ Изменить", callback_data="main:numerology")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text(summary, reply_markup=buttons)
    return CONFIRM


async def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    data = context.user_data.get("num", {})
    payload = {
        "user_id": update.effective_user.id,
        "mode": "numerology",
        "subtype": data.get("subtype"),
        "input": data.get("input", {}),
        "style": data.get("style", "short"),
        "locale": "ru",
        "timezone": "Europe/Kyiv",
    }
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📌 Рекомендации", callback_data="main:numerology")],
            [InlineKeyboardButton("💾 Сохранить", callback_data="history:open")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await shared.ensure_access_or_paywall(update, context, payload, buttons)
    return ConversationHandler.END


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start, pattern=r"^main:numerology$")],
        states={
            SUBTYPE: [CallbackQueryHandler(choose_subtype, pattern=r"^num:sub:")],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birth_date)],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_name),
                CallbackQueryHandler(skip_name, pattern=r"^num:name:skip"),
            ],
            STYLE: [CallbackQueryHandler(set_style, pattern=r"^num:style:")],
            CONFIRM: [CallbackQueryHandler(run_forecast, pattern=r"^num:go")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern=r"^main:numerology$")],
        map_to_parent={ConversationHandler.END: ConversationHandler.END},
        allow_reentry=True,
    )


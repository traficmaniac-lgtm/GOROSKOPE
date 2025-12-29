from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

from handlers import shared

SUBTYPE, QUESTION, STYLE, CONFIRM = range(4)

TAROT_SPREADS = [
    ("1 карта", "one"),
    ("3 карты", "three"),
    ("5 карт", "five"),
    ("Да/Нет", "yesno"),
    ("Отношения", "love"),
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    buttons = [[InlineKeyboardButton(text, callback_data=f"tarot:sub:{code}")] for text, code in TAROT_SPREADS]
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="nav:home")])
    await update.effective_message.reply_text("✨ Таро", reply_markup=InlineKeyboardMarkup(buttons))
    return SUBTYPE


async def choose_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data["tarot"] = {"subtype": update.callback_query.data.split(":")[-1], "input": {}, "style": "short"}
    await update.callback_query.edit_message_text("Твоя тема?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return QUESTION


async def set_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("tarot", {}).setdefault("input", {})["question"] = update.effective_message.text
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("коротко", callback_data="tarot:style:short")],
            [InlineKeyboardButton("подробно", callback_data="tarot:style:full")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Стиль?", reply_markup=buttons)
    return STYLE


async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("tarot", {})["style"] = update.callback_query.data.split(":")[-1]
    return await show_confirm(update, context)


async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("tarot", {})
    summary = (
        "✅ Подтверди:\n"
        f"Расклад: {data.get('subtype')}\n"
        f"Вопрос: {data.get('input', {}).get('question')}\n"
        f"Стиль: {data.get('style')}"
    )
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Рассчитать", callback_data="tarot:go")],
            [InlineKeyboardButton("✏️ Изменить", callback_data="main:tarot")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text(summary, reply_markup=buttons)
    return CONFIRM


async def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    data = context.user_data.get("tarot", {})
    payload = {
        "user_id": update.effective_user.id,
        "mode": "tarot",
        "subtype": data.get("subtype"),
        "input": data.get("input", {}),
        "style": data.get("style", "short"),
        "locale": "ru",
        "timezone": "Europe/Kyiv",
    }
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Перетянуть", callback_data="main:tarot")],
            [InlineKeyboardButton("🧠 Разбор глубже", callback_data="main:tarot")],
            [InlineKeyboardButton("💾 История", callback_data="history:open")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await shared.ensure_access_or_paywall(update, context, payload, buttons)
    return ConversationHandler.END


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start, pattern=r"^main:tarot$")],
        states={
            SUBTYPE: [CallbackQueryHandler(choose_subtype, pattern=r"^tarot:sub:")],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_question)],
            STYLE: [CallbackQueryHandler(set_style, pattern=r"^tarot:style:")],
            CONFIRM: [CallbackQueryHandler(run_forecast, pattern=r"^tarot:go")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern=r"^main:tarot$")],
        map_to_parent={ConversationHandler.END: ConversationHandler.END},
        allow_reentry=True,
    )


from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services import storage


async def open_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    rows = storage.list_history(update.effective_user.id, limit=5)
    if not rows:
        text = "Пока пусто"
    else:
        lines = []
        for row in rows:
            lines.append(f"{row['mode']} / {row['subtype']} — {row['created_at']}")
        text = "\n".join(lines)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Домой", callback_data="nav:home")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb)


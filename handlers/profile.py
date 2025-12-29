from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db
import texts

PROFILE_KB = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("✍️ Заполнить/Изменить", callback_data="profile:edit")],
        [InlineKeyboardButton("🗑️ Сброс", callback_data="profile:reset")],
        [InlineKeyboardButton("⭐ Статус подписки", callback_data="menu:premium")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:home")],
    ]
)


def render_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    profile = db.get_profile(update.effective_user.id)
    lines = ["👤 Профиль"]
    if not profile:
        lines.append(texts.PROFILE_EMPTY)
    else:
        for key, value in profile.items():
            lines.append(f"{key}: {value}")
    sub_text = "Активна" if db.has_subscription(user) else "Нет"
    lines.append(f"Подписка: {sub_text}")
    update.effective_message.reply_text("\n".join(lines), reply_markup=PROFILE_KB)

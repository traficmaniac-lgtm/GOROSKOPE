from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import config
from services import storage


MAIN_BUTTONS = [
    ("🔮 Гороскоп", "main:horoscope"),
    ("🃏 Таро", "main:tarot"),
    ("🔢 Нумерология", "main:numerology"),
    ("💞 Совместимость", "main:compatibility"),
    ("⭐️ Мой пакет / Баланс", "main:package"),
    ("⚙️ Настройки", "main:settings"),
]


def build_menu() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text, callback_data=data)] for text, data in MAIN_BUTTONS]
    return InlineKeyboardMarkup(rows)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage.get_user(update.effective_user.id)
    caption = (
        "✨ Главное меню\n"
        f"Бесплатно: {user['free_remaining']} | ⭐: {user['stars_balance']}"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(caption, reply_markup=build_menu())
    else:
        await update.effective_message.reply_text(caption, reply_markup=build_menu())


async def show_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage.get_user(update.effective_user.id)
    sub_active = storage.subscription_active(user)
    text = (
        "⭐️ Баланс\n"
        f"Free: {user['free_remaining']} из {config.DEFAULT_FREE_REQUESTS}\n"
        f"Stars: {user['stars_balance']}\n"
        f"Подписка: {'✅ активна' if sub_active else '—'}"
    )
    buttons = [
        [InlineKeyboardButton("Купить Stars", callback_data="billing:stars")],
        [InlineKeyboardButton("Подписка", callback_data="billing:sub")],
        [InlineKeyboardButton("История", callback_data="history:open")],
        [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
    ]
    kb = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb)


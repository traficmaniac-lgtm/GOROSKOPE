from __future__ import annotations

from typing import Iterable, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

MAIN_TITLE = "🪐 Главное меню"


def _row(*buttons: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return list(buttons)


def build_main_keyboard(is_new_user: bool) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = [
        _row(
            InlineKeyboardButton("🔮 Гороскоп", callback_data="menu:horoscope"),
            InlineKeyboardButton("🃏 Таро", callback_data="menu:tarot"),
        ),
        _row(
            InlineKeyboardButton("🔢 Нумерология", callback_data="menu:numerology"),
            InlineKeyboardButton("❤️ Совместимость", callback_data="menu:compat"),
        ),
    ]

    profile_buttons: Iterable[InlineKeyboardButton]
    if is_new_user:
        profile_buttons = _row(
            InlineKeyboardButton("⚡️ Быстрый старт", callback_data="onboard:fast"),
            InlineKeyboardButton("👤 Профиль", callback_data="menu:profile"),
        )
    else:
        profile_buttons = _row(
            InlineKeyboardButton("👤 Профиль", callback_data="menu:profile"),
        )
    rows.append(list(profile_buttons))

    rows.extend(
        [
            _row(
                InlineKeyboardButton("⭐️ Премиум-доступ", callback_data="paywall:open"),
                InlineKeyboardButton("🎁 Бонусы", callback_data="bonus:open"),
            ),
            _row(
                InlineKeyboardButton("📌 Избранное", callback_data="fav:open"),
                InlineKeyboardButton("🧭 Помощь", callback_data="help:open"),
            ),
            _row(
                InlineKeyboardButton("🛠 Настройки", callback_data="settings:open"),
                InlineKeyboardButton("ℹ️ О проекте", callback_data="about:open"),
            ),
            _row(
                InlineKeyboardButton("⬅️ Назад", callback_data="nav:back"),
                InlineKeyboardButton("🏠 Меню", callback_data="nav:home"),
            ),
        ]
    )

    return InlineKeyboardMarkup(rows)


async def render_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_user: bool
) -> None:
    keyboard = build_main_keyboard(is_new_user)
    message = update.effective_message

    if update.callback_query:
        await update.callback_query.answer()
        if message:
            try:
                await message.edit_text(MAIN_TITLE, reply_markup=keyboard)
            except Exception:  # noqa: BLE001
                await message.edit_reply_markup(reply_markup=keyboard)
        return

    if message:
        await message.reply_text(MAIN_TITLE, reply_markup=keyboard)


async def respond_placeholder(update: Update, text: str) -> None:
    query = update.callback_query
    if query:
        await query.answer(text=text, show_alert=False)

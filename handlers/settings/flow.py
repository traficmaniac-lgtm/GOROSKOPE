from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services import storage


def _settings_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("👤 Профиль", callback_data="settings:profile")],
        [InlineKeyboardButton("🌐 Язык", callback_data="settings:lang")],
        [InlineKeyboardButton("🕑 Часовой пояс", callback_data="settings:tzone")],
        [InlineKeyboardButton("📝 Формат", callback_data="settings:format")],
        [InlineKeyboardButton("🛡 Приватность", callback_data="settings:privacy")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="settings:help")],
        [InlineKeyboardButton("🎁 Реферал", callback_data="settings:ref")],
        [InlineKeyboardButton("📜 История", callback_data="history:open")],
        [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
    ]
    return InlineKeyboardMarkup(buttons)


async def open_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("⚙️ Настройки", reply_markup=_settings_keyboard())
    else:
        await update.effective_message.reply_text("⚙️ Настройки", reply_markup=_settings_keyboard())


async def handle_settings_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    user = storage.get_user(update.effective_user.id)
    if action == "profile":
        text = "👤 Имя и данные можно добавить позже."
    elif action == "lang":
        text = "🌐 Язык: RU"
    elif action == "tzone":
        text = "🕑 Часовой пояс авто"
    elif action == "format":
        text = "📝 Формат: коротко/подробно на выбор в сценарии"
    elif action == "privacy":
        text = "🛡 История сохраняется локально"
    elif action == "help":
        text = "🆘 support@astro.ai"
    elif action == "ref":
        text = "🎁 Поделись кодом: ASTRO"
    else:
        text = f"⚙️ Free: {user['free_remaining']} ⭐ {user['stars_balance']}"
    await query.edit_message_text(text, reply_markup=_settings_keyboard())


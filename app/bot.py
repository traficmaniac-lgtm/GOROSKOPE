"""Telegram bot for GOROSKOPE."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import LOG_DIR, SETTINGS_FILE, load_config
from app.horoscope import SIGNS
from app.openai_client import HoroscopeClient
from app.storage import Storage

SETTINGS_DEFAULTS: Dict[str, str] = {
    "welcome_message": (
        "Привет! Я GOROSKOPE бот. Используй /today или /week, чтобы получить гороскоп. "
        "Без подписки доступен один бесплатный прогноз в сутки."
    ),
    "system_prompt": (
        "Ты дружелюбный астролог. Пиши лаконичные и вдохновляющие гороскопы, "
        "избегай повторов и клише."
    ),
}

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_settings() -> Dict[str, str]:
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(SETTINGS_DEFAULTS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return dict(SETTINGS_DEFAULTS)
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {**SETTINGS_DEFAULTS, **data}


def build_keyboard(period: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for idx, sign in enumerate(SIGNS, start=1):
        row.append(InlineKeyboardButton(sign, callback_data=f"{period}:{sign}"))
        if idx % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data.get("settings", SETTINGS_DEFAULTS)
    await update.message.reply_text(settings.get("welcome_message", SETTINGS_DEFAULTS["welcome_message"]))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "Команды:\n"
        "/start — приветствие и подсказки\n"
        "/today — гороскоп на сегодня\n"
        "/week — гороскоп на неделю\n"
        "/grant <user_id> <days> — продлить подписку (только админ)"
    )
    await update.message.reply_text(message)


async def request_sign(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str) -> None:
    await update.message.reply_text(
        "Выбери свой знак зодиака:", reply_markup=build_keyboard(period)
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await request_sign(update, context, "today")


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await request_sign(update, context, "week")


async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data.split(":", maxsplit=1)
    if len(data) != 2:
        return
    period, sign = data
    storage: Storage = context.bot_data["storage"]
    user_id = query.from_user.id

    if not storage.can_use(user_id):
        await query.edit_message_text(
            "Бесплатный лимит на сегодня исчерпан. Оформите подписку или попробуйте завтра."
        )
        return

    settings = context.bot_data.get("settings", SETTINGS_DEFAULTS)
    client: HoroscopeClient = context.bot_data["openai_client"]
    await query.edit_message_text("Готовлю прогноз...")
    try:
        text = await asyncio.to_thread(client.generate, sign, period, settings["system_prompt"])
        storage.mark_used(user_id)
        await query.edit_message_text(text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка генерации гороскопа")
        await query.edit_message_text(f"Не удалось получить гороскоп: {exc}")


async def grant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config_admin = context.bot_data.get("admin_id")
    if config_admin is None or update.effective_user.id != config_admin:
        await update.message.reply_text("Доступ запрещён.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Использование: /grant <user_id> <days>")
        return
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("user_id и days должны быть числами")
        return
    storage: Storage = context.bot_data["storage"]
    storage.grant_subscription(user_id, days)
    await update.message.reply_text(
        f"Подписка пользователя {user_id} продлена на {days} дн."
    )


def build_application() -> Application:
    setup_logging()
    config = load_config()
    if not config.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан. Укажите его в .env.")
    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY не задан. Укажите его в .env.")

    settings = load_settings()
    storage = Storage()
    client = HoroscopeClient(config.openai_api_key, config.openai_model)

    application = (
        Application.builder()
        .token(config.telegram_bot_token)
        .concurrent_updates(True)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["storage"] = storage
    application.bot_data["openai_client"] = client
    application.bot_data["admin_id"] = config.admin_telegram_id

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("grant", grant))
    application.add_handler(CallbackQueryHandler(handle_selection, pattern=r"^(today|week):"))
    return application


def main() -> None:
    application = build_application()
    logger.info("GOROSKOPE bot is starting")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


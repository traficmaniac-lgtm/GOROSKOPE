"""Minimal Telegram bot for verifying OpenAI connectivity."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    AIORateLimiter,
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.openai_client import OpenAIClient

ASK_PROMPT = 1
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "db.json"
DEFAULT_MODEL = "gpt-4o-mini"

logger = logging.getLogger(__name__)


def load_settings() -> Tuple[str, str, str, str]:
    load_dotenv(dotenv_path=ENV_FILE)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    admin_id = os.getenv("ADMIN_TELEGRAM_ID", "")
    return token, openai_key, model, admin_id


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        DB_FILE.write_text("{}", encoding="utf-8")


def build_application() -> Application:
    token, openai_key, model, admin_id = load_settings()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан. Заполни .env через UI и перезапусти бота.")

    application = (
        Application.builder()
        .token(token)
        .rate_limiter(AIORateLimiter())
        .concurrent_updates(True)
        .build()
    )

    application.bot_data["openai_key"] = openai_key
    application.bot_data["openai_model"] = model or DEFAULT_MODEL
    application.bot_data["admin_id"] = admin_id

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(build_ai_handler())

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Бот онлайн. Нажми /ping для проверки или /ai чтобы отправить запрос в OpenAI."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("pong")


async def ai_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.bot_data.get("openai_key"):
        await update.message.reply_text("OpenAI ключ не задан. Заполни .env через UI и перезапусти бота.")
        return ConversationHandler.END

    await update.message.reply_text("Напиши запрос для ИИ")
    return ASK_PROMPT


async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_prompt = update.message.text
    openai_key = context.bot_data.get("openai_key")
    model = context.bot_data.get("openai_model", DEFAULT_MODEL)

    if not openai_key:
        await update.message.reply_text("OpenAI ключ не задан. Заполни .env через UI и перезапусти бота.")
        return ConversationHandler.END

    client = OpenAIClient(openai_key, model)
    await update.message.reply_text("Думаю над ответом...")

    try:
        response_text = await context.application.run_in_threadpool(client.ask, user_prompt)
        await update.message.reply_text(response_text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка запроса к OpenAI")
        await update.message.reply_text(f"Не удалось получить ответ от OpenAI: {exc}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def build_ai_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("ai", ai_entry)],
        states={ASK_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    ensure_data_files()
    application = build_application()
    logger.info("Bot is starting")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

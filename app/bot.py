"""Telegram bot for delivering daily horoscopes via OpenAI."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.openai_client import OpenAIClient

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "db.json"
DEFAULT_MODEL = "gpt-4o-mini"
FREE_USES = 3

SYSTEM_PROMPT = "Ты мистический астролог. Пиши красиво, но без обещаний денег, здоровья или судьбы."
USER_PROMPT_TEMPLATE = (
    "Гороскоп на сегодня для знака {sign}.\n"
    "Стиль: загадочный, тёплый, мотивирующий.\n"
    "Длина: 5–7 предложений."
)

ZODIAC_SIGNS = [
    "Овен",
    "Телец",
    "Близнецы",
    "Рак",
    "Лев",
    "Дева",
    "Весы",
    "Скорпион",
    "Стрелец",
    "Козерог",
    "Водолей",
    "Рыбы",
]

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


def load_users() -> Dict[str, Dict[str, str | int]]:
    try:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_users(data: Dict[str, Dict[str, str | int]]) -> None:
    DB_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_user(user_id: int) -> Dict[str, str | int]:
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "user_id": uid,
            "zodiac": "",
            "birth_date": "",
            "free_uses": FREE_USES,
            "created_at": datetime.utcnow().isoformat(),
        }
        save_users(users)
    return users[uid]


def update_user(uid: str, **changes: str | int) -> None:
    users = load_users()
    if uid not in users:
        return
    users[uid].update(changes)
    save_users(users)


def build_keyboard() -> ReplyKeyboardMarkup:
    rows = [ZODIAC_SIGNS[i : i + 3] for i in range(0, len(ZODIAC_SIGNS), 3)]
    buttons = [[KeyboardButton(text=sign) for sign in row] for row in rows]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def build_application() -> Application:
    token, openai_key, model, admin_id = load_settings()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан. Заполни .env через UI и перезапусти бота.")

    application = (
        Application.builder()
        .token(token)
        .concurrent_updates(True)
        .build()
    )

    application.bot_data["openai_key"] = openai_key
    application.bot_data["openai_model"] = model or DEFAULT_MODEL
    application.bot_data["admin_id"] = admin_id

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("test", test_openai))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_zodiac))

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ensure_user(update.effective_user.id)
    greeting = (
        "🔮 Добро пожаловать в GOROSKOPE!\n\n"
        "Я мистический астролог-ассистент. Задавай вопросы и получай подсказки,"
        " но помни: это творческое развлечение, а не предсказание судьбы.\n\n"
        "У тебя есть 3 бесплатных прогноза на день. Выбери свой знак зодиака кнопкой ниже,"
        " и я составлю загадочный дневной гороскоп."
    )
    await update.message.reply_text(greeting, reply_markup=build_keyboard())


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("pong")


async def test_openai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    openai_key = context.bot_data.get("openai_key")
    model = context.bot_data.get("openai_model", DEFAULT_MODEL)

    if not openai_key:
        await update.message.reply_text("OpenAI ключ не задан. Заполни .env через UI и перезапусти бота.")
        return

    client = OpenAIClient(openai_key, model)
    await update.message.reply_text("Отправляю тестовый запрос в OpenAI...")

    try:
        reply = await context.application.run_in_threadpool(client.test_greeting)
        await update.message.reply_text(f"OpenAI: {reply}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка запроса к OpenAI")
        await update.message.reply_text(f"Не удалось получить ответ от OpenAI: {exc}")


def build_prompt(sign: str) -> str:
    user_prompt = USER_PROMPT_TEMPLATE.format(sign=sign)
    return f"SYSTEM:\n{SYSTEM_PROMPT}\n\nUSER:\n{user_prompt}"


async def handle_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    match = next((s for s in ZODIAC_SIGNS if s.lower() == text.lower()), None)

    if not match:
        await update.message.reply_text(
            "Используй кнопки, чтобы выбрать свой знак зодиака.",
            reply_markup=build_keyboard(),
        )
        return

    openai_key = context.bot_data.get("openai_key")
    model = context.bot_data.get("openai_model", DEFAULT_MODEL)
    if not openai_key:
        await update.message.reply_text(
            "OpenAI ключ не задан. Сохрани настройки через UI и перезапусти бота.",
            reply_markup=build_keyboard(),
        )
        return

    user = ensure_user(update.effective_user.id)
    if user.get("free_uses", 0) <= 0:
        await update.message.reply_text("Скоро подписка ✨", reply_markup=build_keyboard())
        return

    client = OpenAIClient(openai_key, model)
    prompt = build_prompt(match)
    await update.message.reply_text("Плету звёздный прогноз... ✨")

    try:
        horoscope = await context.application.run_in_threadpool(client.ask, prompt)
        remaining = max(int(user.get("free_uses", 0)) - 1, 0)
        update_user(user["user_id"], zodiac=match, free_uses=remaining)
        await update.message.reply_text(
            f"{horoscope}\n\nОсталось бесплатных прогнозов: {remaining}.",
            reply_markup=build_keyboard(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка запроса к OpenAI")
        await update.message.reply_text(
            f"Не удалось получить гороскоп: {exc}", reply_markup=build_keyboard()
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

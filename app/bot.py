"""Telegram bot delivering horoscopes via OpenAI."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from app import profile_flow, storage
from callbacks import router
from services.payments import stars
from services.users import profile as user_profile
from ui.menus import main_menu
from app.openai_client import OpenAIClient

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "Ты — профессиональный астролог и копирайтер. Пиши по-русски. Без обещаний. "
    "Без медицины/финансовых гарантий. Структура: Заголовок + 5 буллетов + совет дня + цвета/числа."
)

logger = logging.getLogger(__name__)


def load_settings() -> tuple[str, str, str, str]:
    load_dotenv(dotenv_path=ENV_FILE)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    admin_id = os.getenv("ADMIN_TELEGRAM_ID", "")
    return token, openai_key, model, admin_id


def build_application() -> Application:
    token, openai_key, model, admin_id = load_settings()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан. Заполни .env через UI и перезапусти бота.")

    app = Application.builder().token(token).concurrent_updates(True).build()
    app.bot_data.update({
        "openai_key": openai_key,
        "openai_model": model or DEFAULT_MODEL,
        "admin_id": admin_id,
    })

    # Profile conversation
    app.add_handler(profile_flow.build_handler())

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("reset", reset_profile))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("me", show_profile))
    app.add_handler(CommandHandler("grant", grant_subscription))
    app.add_handler(CommandHandler("test", test_openai))
    app.add_handler(CommandHandler("ping", ping))

    # Callback router
    for handler in router.build_handlers():
        app.add_handler(handler)

    # Payments
    app.add_handler(PreCheckoutQueryHandler(stars.handle_precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, stars.handle_successful_payment))

    app.add_error_handler(error_handler)

    return app


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = user_profile.ensure_user(update.effective_user.id)
    is_new = user_profile.is_first_time(user)
    await main_menu.render_start_screen(update, context, is_new)
    user_profile.mark_returning(update.effective_user.id)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("pong")


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage.get_user(update.effective_user.id)
    profile = storage.Profile.from_dict(user.get("profile"))
    summary = storage.profile_summary(profile)
    free_left = user.get("free_uses", storage.DEFAULT_FREE_USES)
    sub_until = int(user.get("premium_until") or user.get("sub_until", 0))
    lifetime = bool(user.get("premium_lifetime"))
    sub_text = "Есть активная" if storage.has_premium(user) else "Нет"
    if lifetime:
        sub_text += " (навсегда)"
    elif sub_until:
        sub_text += f" (до {datetime.fromtimestamp(sub_until).strftime('%d.%m.%Y')})"

    await update.message.reply_text(
        f"Твой профиль:\n{summary}\n\n"
        f"Бесплатных прогнозов осталось: {free_left}\n"
        f"Подписка: {sub_text}\n"
        "Команда /start перезапустит анкету.",
    )


async def reset_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.reset_profile(update.effective_user.id)
    await update.message.reply_text(
        "Профиль очищен. Запусти /start, чтобы настроить заново.",
    )


def _build_prompt(profile: storage.Profile, theme: str, period: str) -> str:
    period_text = "сегодня" if period == "today" else "неделю"
    lines = [
        SYSTEM_PROMPT,
        "\nДанные клиента:",
        f"Имя: {profile.name or '—'}",
        f"Пол: {profile.gender or '—'}",
        f"Дата рождения: {profile.birth_date or '—'}",
        f"Время рождения: {profile.birth_time or '—'}",
        f"Город: {profile.city or '—'}",
        f"Знак зодиака: {profile.sign or '—'}",
        f"Тема запроса: {theme}",
        f"Период: {period_text}",
        "Сделай текст тёплым и мистическим, но без обещаний.",
    ]
    return "\n".join(lines)


def _get_client(context: ContextTypes.DEFAULT_TYPE) -> OpenAIClient:
    openai_key = context.bot_data.get("openai_key")
    model = context.bot_data.get("openai_model", DEFAULT_MODEL)
    if not openai_key:
        raise RuntimeError("OpenAI ключ не задан. Сохрани .env через UI.")
    return OpenAIClient(openai_key, model)


async def _generate_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str) -> None:
    user = storage.get_user(update.effective_user.id)
    profile = storage.Profile.from_dict(user.get("profile"))

    if not profile.sign:
        await update.message.reply_text("Сначала запусти /start и выбери знак зодиака.")
        return

    theme = profile.theme or profile_flow.THEME_OPTIONS[0]
    try:
        client = _get_client(context)
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(str(exc))
        return

    if not storage.has_premium(user) and int(user.get("free_uses", 0)) <= 0:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Связаться / Оплата скоро", url="https://t.me/")]]
        )
        await update.message.reply_text(
            "Бесплатный лимит исчерпан. Подписка скоро, но можно связаться.", reply_markup=keyboard
        )
        return

    prompt = _build_prompt(profile, theme, period)
    await update.message.reply_text("Плету звёздный прогноз... ✨")

    try:
        horoscope = await asyncio.to_thread(client.ask, prompt)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка запроса к OpenAI")
        await update.message.reply_text(f"Не удалось получить гороскоп: {exc}")
        return

    remaining = user.get("free_uses", storage.DEFAULT_FREE_USES)
    if not storage.has_premium(user):
        remaining = storage.decrement_free_use(update.effective_user.id)

    await update.message.reply_text(
        f"{horoscope}\n\nОсталось бесплатных прогнозов: {remaining}",
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _generate_forecast(update, context, period="today")


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _generate_forecast(update, context, period="week")


async def test_openai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        client = _get_client(context)
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(str(exc))
        return

    await update.message.reply_text("Отправляю тестовый запрос в OpenAI...")
    try:
        reply = await asyncio.to_thread(client.test_greeting)
        await update.message.reply_text(f"OpenAI: {reply}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ошибка запроса к OpenAI")
        await update.message.reply_text(f"Не удалось получить ответ от OpenAI: {exc}")


async def grant_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = str(context.bot_data.get("admin_id") or "")
    if not admin_id or str(update.effective_user.id) != admin_id:
        await update.message.reply_text("Команда доступна только админу.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Используй: /grant <user_id> <days>")
        return

    target_id, days = context.args[0], context.args[1]
    if not target_id.isdigit() or not days.isdigit():
        await update.message.reply_text("user_id и days должны быть числами.")
        return

    until_ts = storage.grant_subscription(int(target_id), int(days))
    until_text = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
    await update.message.reply_text(f"Подписка пользователю {target_id} до {until_text}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while handling update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Упс, что-то пошло не так. Попробуй ещё раз позже.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    storage.ensure_data_file()
    app = build_application()
    logger.info("Bot is starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

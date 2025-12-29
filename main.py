from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
)

import config
from handlers import history, shared
from handlers.compatibility import flow as compat_flow
from handlers.horoscope import flow as horo_flow
from handlers.main_menu import show_menu, show_package
from handlers.numerology import flow as num_flow
from handlers.settings import flow as settings_flow
from handlers.tarot import flow as tarot_flow
from services import storage

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_menu(update, context)


async def nav_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    await show_menu(update, context)
    return ConversationHandler.END


def build_application() -> Application:
    storage.init_storage()
    application = Application.builder().token(config.TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(horo_flow.build_conversation())
    application.add_handler(tarot_flow.build_conversation())
    application.add_handler(num_flow.build_conversation())
    application.add_handler(compat_flow.build_conversation())

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_package, pattern=r"^main:package"))
    application.add_handler(CallbackQueryHandler(settings_flow.open_settings, pattern=r"^main:settings"))
    application.add_handler(CallbackQueryHandler(show_menu, pattern=r"^main:(horoscope|tarot|numerology|compatibility)$", block=False))
    application.add_handler(CallbackQueryHandler(settings_flow.handle_settings_action, pattern=r"^settings:"))
    application.add_handler(CallbackQueryHandler(history.open_history, pattern=r"^history:open"))
    application.add_handler(CallbackQueryHandler(shared.handle_payment_choice, pattern=r"^pay:"))
    application.add_handler(CallbackQueryHandler(nav_home, pattern=r"^nav:home"))

    return application


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = build_application()
    logger.info("Bot starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


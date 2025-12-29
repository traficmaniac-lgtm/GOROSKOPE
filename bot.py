from __future__ import annotations

import asyncio
import logging
import sys
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent, Update

from app.config.settings import settings
from app.core.logging import setup_logging
from app.core.router import setup_routers
from app.db.storage import Database
from app.modules.horoscope.handlers import init_horoscope_services
from app.services.ai_service import AIServiceError, resolve_ai_service
from app.services.health import StartupError, perform_startup_checks
from app.services.payment_service import StubPaymentService
from app.services.quota_service import QuotaService


async def main() -> None:
    log_file = setup_logging()
    logger = logging.getLogger("bot")
    try:
        perform_startup_checks()
    except StartupError:
        logger.error("Бот остановлен из-за некорректных настроек.")
        logger.info("Подробности см. в %s", log_file)
        return

    db = Database(settings.db_path)
    await db.init()

    quota_service = QuotaService(db)
    ai_resolution = resolve_ai_service()
    payment_service = StubPaymentService()
    init_horoscope_services(quota_service, ai_resolution.service, payment_service, mode=ai_resolution.mode)

    if ai_resolution.mode == "stub":
        logger.warning("AI работает в режиме STUB, подключение OpenAI отключено или недоступно")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    @dp.errors()
    async def global_error_handler(event: ErrorEvent, bot: Bot) -> bool:  # pragma: no cover - runtime guard
        logger.error("Unhandled error: %s", event.exception, exc_info=event.exception)
        traceback.print_exception(type(event.exception), event.exception, event.exception.__traceback__)

        message_text = "Произошла ошибка, попробуйте снова." if not isinstance(event.exception, AIServiceError) else str(event.exception)
        update: Update | None = event.update
        if update:
            target = update.message or (update.callback_query.message if update.callback_query else None)
            if target:
                try:
                    await target.answer(message_text)
                except Exception:
                    logger.exception("Failed to send error message to user")
        return True

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

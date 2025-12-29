from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config.settings import settings
from app.core.logging import setup_logging
from app.core.router import setup_routers
from app.db.storage import Database
from app.modules.horoscope.handlers import init_horoscope_services
from app.services.ai_service import resolve_ai_service
from app.services.payment_service import StubPaymentService
from app.services.quota_service import QuotaService


def check_token(token: str) -> None:
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Установите его в .env или переменную окружения.")


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("bot")

    check_token(settings.bot_token)

    db = Database(settings.db_path)
    await db.init()

    quota_service = QuotaService(db)
    ai_service = resolve_ai_service()
    payment_service = StubPaymentService()
    init_horoscope_services(quota_service, ai_service, payment_service)

    bot = Bot(token=settings.bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

from aiogram import Router

from app.modules.horoscope.handlers import horoscope_router


def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(horoscope_router)
    return main_router

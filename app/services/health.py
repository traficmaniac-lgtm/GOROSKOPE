from __future__ import annotations

import logging
import socket
import sys
from typing import Iterable

from app.config.settings import settings
from app.services.ai_service import check_network_host

logger = logging.getLogger(__name__)


def _check_token(token: str) -> None:
    if not token:
        logger.error("BOT_TOKEN не задан. Установите его в .env или переменную окружения.")
        sys.exit(1)


def _check_openai_key() -> None:
    if settings.use_openai and not settings.openai_api_key:
        logger.warning("USE_OPENAI=true, но OPENAI_API_KEY пуст. Будет использован StubAIService.")


def _check_network() -> None:
    targets: Iterable[tuple[str, int, str]] = [
        ("api.telegram.org", 443, "Telegram"),
    ]
    if settings.use_openai and settings.openai_api_key:
        targets = [
            *targets,
            ("api.openai.com", 443, "OpenAI"),
        ]
    for host, port, name in targets:
        if not check_network_host(host, port):
            logger.warning("Не удалось подключиться к %s (%s:%s). Проверьте сеть.", name, host, port)
        else:
            logger.info("%s доступен (%s:%s)", name, host, port)


def perform_startup_checks() -> None:
    _check_token(settings.bot_token)
    _check_openai_key()
    _check_network()

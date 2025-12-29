from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RuntimeConfig:
    """Lightweight runtime configuration layer for user overrides."""

    def __init__(self) -> None:
        self.overrides_path = Path(settings.overrides_path)
        self.free_quota: int = settings.free_quota
        self.request_price_stars: int = settings.request_price_stars
        self.text_overrides: dict[str, str] = {}
        self.prompt_style: dict[str, Any] = {}
        self._load_overrides()

    def _load_overrides(self) -> None:
        if not self.overrides_path.exists():
            return
        try:
            data = json.loads(self.overrides_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.warning("Failed to read overrides: %s", exc)
            return

        self.free_quota = int(data.get("FREE_QUOTA", self.free_quota))
        self.request_price_stars = int(data.get("REQUEST_PRICE_STARS", self.request_price_stars))
        self.text_overrides = data.get("TEXTS", {}) or {}
        prompt_style = data.get("HOROSCOPE_PROMPT_STYLE", {}) or {}
        self.prompt_style = {
            "tone": prompt_style.get("tone"),
            "bullets": prompt_style.get("bullets"),
            "bullets_count": prompt_style.get("bullets_count", prompt_style.get("bullets")),
        }

    def reload(self) -> None:
        self.free_quota = settings.free_quota
        self.request_price_stars = settings.request_price_stars
        self.text_overrides = {}
        self.prompt_style = {}
        self._load_overrides()


runtime_config = RuntimeConfig()


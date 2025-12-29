"""Configuration loading for GOROSKOPE bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
SETTINGS_FILE = DATA_DIR / "bot_settings.json"
DB_FILE = DATA_DIR / "db.json"


def ensure_directories() -> None:
    """Ensure required directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_env() -> None:
    """Load environment variables from .env if present."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)


@dataclass
class Config:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    admin_telegram_id: Optional[int]


DEFAULT_MODEL = "gpt-4o-mini"


def load_config() -> Config:
    """Load configuration values from the environment."""
    ensure_directories()
    load_env()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    admin_id_raw = os.getenv("ADMIN_TELEGRAM_ID", "")
    admin_id = int(admin_id_raw) if admin_id_raw.strip().isdigit() else None

    return Config(
        telegram_bot_token=token,
        openai_api_key=openai_key,
        openai_model=model,
        admin_telegram_id=admin_id,
    )


def update_env_file(**kwargs: str) -> None:
    """Update the .env file with provided key-value pairs."""
    ensure_directories()
    existing = {}
    if ENV_FILE.exists():
        with ENV_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v
    for key, value in kwargs.items():
        existing[key] = value
    content = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
    with ENV_FILE.open("w", encoding="utf-8") as f:
        f.write(content)


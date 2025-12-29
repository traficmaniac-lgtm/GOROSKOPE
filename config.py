from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "bot.sqlite"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DEFAULT_FREE_REQUESTS = 3
SUBSCRIPTION_DAYS = 30

# Pricing
OPENAI_IN_PER_1K = float(os.getenv("OPENAI_IN_PER_1K", 0.005))
OPENAI_OUT_PER_1K = float(os.getenv("OPENAI_OUT_PER_1K", 0.015))
USD_PER_STAR = float(os.getenv("USD_PER_STAR", 0.02))
MIN_STARS_PER_REQUEST = 2
MAX_STARS_PER_REQUEST = 50

ESTIMATED_COMPLETION = {
    "horoscope": 700,
    "tarot": 600,
    "numerology": 800,
    "compat": 900,
}

FLOW_STATES = {
    "SELECT": 1,
    "INPUT_1": 2,
    "INPUT_2": 3,
    "PREVIEW": 4,
    "PAYWALL": 5,
    "RUN_AI": 6,
    "RESULT": 7,
}

SUBSCRIPTION_DELTA = timedelta(days=SUBSCRIPTION_DAYS)

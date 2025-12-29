"""Billing helper for free limits, stars and subscription access."""
from __future__ import annotations

import time
from typing import Dict

import config
from services import storage


COMPLEXITY_PRICING = {
    "horoscope": 3,
    "tarot": 2,
    "numerology": 2,
    "compatibility": 4,
}


def price_for_mode(mode: str) -> int:
    base = COMPLEXITY_PRICING.get(mode, 2)
    return base * 3


def estimate_stars(prompt_len: int, model: str | None = None) -> int:
    del model
    tokens = max(prompt_len // 4, 1)
    return max(tokens // 100, 1)


def can_access(user_row: Dict, price: int) -> bool:
    if storage.subscription_active(user_row):
        return True
    if int(user_row.get("free_remaining", 0)) > 0:
        return True
    return int(user_row.get("stars_balance", 0)) >= price


def consume(user_id: int, price: int) -> None:
    user = storage.get_user(user_id)
    if storage.subscription_active(user):
        return
    if int(user["free_remaining"]) > 0:
        storage.adjust_balance(user_id, free_delta=-1)
        return
    if int(user["stars_balance"]) >= price:
        storage.adjust_balance(user_id, stars_delta=-price)


def grant_stars(user_id: int, stars: int) -> None:
    storage.adjust_balance(user_id, stars_delta=stars)


def grant_subscription_days(user_id: int, days: int = 30) -> None:
    now = int(time.time())
    until = now + days * 86400
    current = storage.get_user(user_id)["subscription_until"] or 0
    storage.set_subscription(user_id, max(current, now) + days * 86400 if current > now else until)


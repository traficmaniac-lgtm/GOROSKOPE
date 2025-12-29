from __future__ import annotations

import math
import time
from typing import Tuple

import config
import db


def estimate_price(module: str, text_len: int) -> Tuple[int, float]:
    estimated_prompt_tokens = max(50, text_len // 4)
    completion_tokens = config.ESTIMATED_COMPLETION.get(module, 600)
    cost_usd = (estimated_prompt_tokens / 1000) * config.OPENAI_IN_PER_1K + (
        completion_tokens / 1000
    ) * config.OPENAI_OUT_PER_1K
    price_usd = cost_usd * 3
    stars = math.ceil(price_usd / config.USD_PER_STAR)
    stars = min(max(stars, config.MIN_STARS_PER_REQUEST), config.MAX_STARS_PER_REQUEST)
    return stars, cost_usd


def consume_access(user_row) -> bool:
    if db.has_subscription(user_row):
        return True
    if user_row["paid_credits"] > 0:
        db.spend_paid_credit(user_row["tg_id"])
        return True
    if user_row["free_ai_left"] > 0:
        db.decrement_free(user_row["tg_id"])
        return True
    return False


def grant_subscription_month(tg_id: int) -> int:
    until_ts = int(time.time() + config.SUBSCRIPTION_DELTA.total_seconds())
    db.grant_subscription(tg_id, until_ts)
    return until_ts


def add_credit(tg_id: int, count: int = 1) -> None:
    db.add_paid_credit(tg_id, count)

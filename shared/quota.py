from __future__ import annotations

"""Simple quota helper on top of storage."""

from typing import Tuple

from services import billing_service, storage


def can_use_free(user_id: int) -> bool:
    user = storage.get_user(user_id)
    return int(user.get("free_remaining", 0)) > 0


def consume_free(user_id: int) -> int:
    storage.adjust_balance(user_id, free_delta=-1)
    return int(storage.get_user(user_id).get("free_remaining", 0))


def ensure_payment(user_id: int, payload_prompt_len: int, model: str) -> Tuple[bool, int]:
    """Return (allowed, price_stars)."""
    price = billing_service.estimate_stars(payload_prompt_len, model) * 3
    user = storage.get_user(user_id)
    if billing_service.can_access(user, price):
        billing_service.consume(user_id, price)
        return True, price
    return False, price

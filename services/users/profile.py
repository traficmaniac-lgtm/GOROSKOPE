from __future__ import annotations

from typing import Dict, Union

from app import storage

UserDict = Dict[str, object]


def ensure_user(user_id: int) -> UserDict:
    return storage.get_user(user_id)


def is_first_time(user: UserDict) -> bool:
    return bool(user.get("is_new", False))


def mark_returning(user_id: int) -> None:
    user = storage.get_user(user_id)
    user["is_new"] = False
    storage.save_user(user_id, user)


def has_premium(user_or_id: Union[int, UserDict]) -> bool:
    user = user_or_id if isinstance(user_or_id, dict) else storage.get_user(int(user_or_id))
    return storage.has_premium(user)

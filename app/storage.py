"""Simple JSON storage for subscriptions and limits."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional

from app.config import DB_FILE, ensure_directories


class Storage:
    """Manage user subscription and daily limits."""

    def __init__(self, path: Path | None = None) -> None:
        ensure_directories()
        self.path = path or DB_FILE
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                json.dump({"users": {}}, f)

    def _load(self) -> Dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_user(self, user_id: int) -> Dict:
        data = self._load()
        users = data.setdefault("users", {})
        return users.setdefault(str(user_id), {"sub_until": 0, "free_day": 0})

    def grant_subscription(self, user_id: int, days: int) -> None:
        data = self._load()
        users = data.setdefault("users", {})
        user = users.setdefault(str(user_id), {"sub_until": 0, "free_day": 0})
        now = int(time.time())
        current = user.get("sub_until", 0)
        base = current if current > now else now
        user["sub_until"] = base + days * 86400
        data["users"] = users
        self._save(data)

    def can_use(self, user_id: int) -> bool:
        user = self._get_user(user_id)
        if user.get("sub_until", 0) > int(time.time()):
            return True
        today = int(time.strftime("%Y%m%d"))
        return user.get("free_day") != today

    def mark_used(self, user_id: int) -> None:
        data = self._load()
        users = data.setdefault("users", {})
        user = users.setdefault(str(user_id), {"sub_until": 0, "free_day": 0})
        if user.get("sub_until", 0) <= int(time.time()):
            user["free_day"] = int(time.strftime("%Y%m%d"))
        data["users"] = users
        self._save(data)

    def subscription_until(self, user_id: int) -> Optional[int]:
        user = self._get_user(user_id)
        return user.get("sub_until")


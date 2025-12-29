"""Persistent JSON storage for user profiles and usage counters."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, MutableMapping

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "db.json"
DEFAULT_FREE_USES = 3


@dataclass
class Profile:
    name: str = ""
    gender: str = ""
    birth_date: str = ""
    birth_time: str = ""
    city: str = ""
    sign: str = ""
    theme: str = ""

    @classmethod
    def from_dict(cls, data: MutableMapping[str, str] | None) -> "Profile":
        data = data or {}
        return cls(
            name=str(data.get("name", "")),
            gender=str(data.get("gender", "")),
            birth_date=str(data.get("birth_date", "")),
            birth_time=str(data.get("birth_time", "")),
            city=str(data.get("city", "")),
            sign=str(data.get("sign", "")),
            theme=str(data.get("theme", "")),
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "birth_time": self.birth_time,
            "city": self.city,
            "sign": self.sign,
            "theme": self.theme,
        }


def ensure_data_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        DB_FILE.write_text("{}", encoding="utf-8")


def _load_db() -> Dict[str, Dict]:
    ensure_data_file()
    try:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save_db(db: Dict[str, Dict]) -> None:
    ensure_data_file()
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_user(user_id: int) -> Dict:
    return {
        "user_id": str(user_id),
        "profile": Profile().to_dict(),
        "free_uses": DEFAULT_FREE_USES,
        "sub_until": 0,
        "premium_until": 0,
        "premium_lifetime": False,
        "is_premium": False,
        "is_new": True,
        "last_payment_charge_id": "",
        "telegram_payment_charge_id": "",
        "last_choice": "",
        "created_at": int(time.time()),
    }


def get_user(user_id: int) -> Dict:
    db = _load_db()
    key = str(user_id)
    if key not in db:
        db[key] = _default_user(user_id)
        _save_db(db)
    user = db[key]
    user.setdefault("last_choice", "")
    user.setdefault("premium_until", 0)
    user.setdefault("premium_lifetime", False)
    user.setdefault("is_premium", False)
    user.setdefault("is_new", False)
    user.setdefault("last_payment_charge_id", "")
    user.setdefault("telegram_payment_charge_id", "")
    return user


def save_user(user_id: int, data: Dict) -> None:
    db = _load_db()
    db[str(user_id)] = data
    _save_db(db)


def update_profile(user_id: int, profile: Profile) -> None:
    user = get_user(user_id)
    user["profile"] = profile.to_dict()
    save_user(user_id, user)


def reset_profile(user_id: int) -> None:
    user = get_user(user_id)
    user["profile"] = Profile().to_dict()
    user["free_uses"] = DEFAULT_FREE_USES
    user.setdefault("sub_until", 0)
    user.setdefault("premium_until", 0)
    user.setdefault("premium_lifetime", False)
    user.setdefault("is_premium", False)
    user.setdefault("is_new", False)
    user.setdefault("last_choice", "")
    save_user(user_id, user)


def update_last_choice(user_id: int, choice: str) -> None:
    user = get_user(user_id)
    user["last_choice"] = choice
    save_user(user_id, user)


def decrement_free_use(user_id: int) -> int:
    user = get_user(user_id)
    remaining = max(int(user.get("free_uses", 0)) - 1, 0)
    user["free_uses"] = remaining
    save_user(user_id, user)
    return remaining


def grant_subscription(user_id: int, days: int) -> int:
    user = get_user(user_id)
    now = int(time.time())
    seconds = days * 86400
    current_until = int(user.get("sub_until", 0))
    new_until = max(current_until, now) + seconds
    user["sub_until"] = new_until
    save_user(user_id, user)
    return new_until


def has_subscription(user: Dict) -> bool:
    return int(user.get("sub_until", 0)) > int(time.time())


def has_premium(user: Dict) -> bool:
    now = int(time.time())
    if user.get("premium_lifetime"):
        return True
    if user.get("is_premium") and int(user.get("premium_until", 0)) == 0:
        return True
    if int(user.get("premium_until", 0)) > now:
        return True
    return has_subscription(user)


def profile_summary(profile: Profile) -> str:
    parts = [
        f"Имя: {profile.name or '—'}",
        f"Пол: {profile.gender or '—'}",
        f"Дата рождения: {profile.birth_date or '—'}",
        f"Время рождения: {profile.birth_time or '—'}",
        f"Город: {profile.city or '—'}",
        f"Знак: {profile.sign or '—'}",
        f"Тема: {profile.theme or '—'}",
    ]
    return "\n".join(parts)

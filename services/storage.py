"""Storage helpers for users, drafts and history using sqlite."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cur = conn.execute(
        "SELECT name FROM pragma_table_info(?) WHERE name = ?", (table, column)
    )
    if not cur.fetchone():
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_storage() -> None:
    Path(config.DATA_DIR).mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                free_remaining INTEGER DEFAULT ?,
                stars_balance INTEGER DEFAULT 0,
                subscription_until INTEGER DEFAULT 0,
                settings_json TEXT DEFAULT '{}'
            )
            """,
            (config.DEFAULT_FREE_REQUESTS,),
        )

        _ensure_column(conn, "users", "stars_balance", "INTEGER DEFAULT 0")
        _ensure_column(conn, "users", "subscription_until", "INTEGER DEFAULT 0")
        _ensure_column(conn, "users", "settings_json", "TEXT DEFAULT '{}' ")
        _ensure_column(conn, "users", "free_remaining", "INTEGER DEFAULT 0")
        _ensure_column(conn, "history", "is_favorite", "INTEGER DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mode TEXT,
                subtype TEXT,
                payload_json TEXT,
                answer TEXT,
                created_at INTEGER,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                price_stars INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mode TEXT,
                subtype TEXT,
                payload_json TEXT,
                created_at INTEGER
            )
            """
        )
        conn.commit()


def get_user(user_id: int) -> Dict:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO users (user_id, free_remaining, stars_balance, subscription_until, settings_json) "
            "VALUES (?, ?, 0, 0, '{}')",
            (user_id, config.DEFAULT_FREE_REQUESTS),
        )
        conn.commit()
        return get_user(user_id)


def update_user(user_id: int, **kwargs: Any) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    with _connect() as conn:
        conn.execute(f"UPDATE users SET {fields} WHERE user_id = ?", values)
        conn.commit()


def adjust_balance(user_id: int, free_delta: int = 0, stars_delta: int = 0) -> sqlite3.Row:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET free_remaining = MAX(free_remaining + ?, 0), "
            "stars_balance = MAX(stars_balance + ?, 0) WHERE user_id = ?",
            (free_delta, stars_delta, user_id),
        )
        conn.commit()
    return get_user(user_id)


def set_subscription(user_id: int, until_ts: int) -> None:
    update_user(user_id, subscription_until=until_ts)


def subscription_active(user: Dict) -> bool:
    return int(user.get("subscription_until", 0) or 0) > int(time.time())


def save_history(
    user_id: int,
    mode: str,
    subtype: str,
    payload: Dict[str, Any],
    answer: str,
    tokens: Tuple[int, int],
    price_stars: int,
    is_favorite: bool = False,
) -> int:
    now = int(time.time())
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO history (user_id, mode, subtype, payload_json, answer, created_at, tokens_in, tokens_out, price_stars, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                mode,
                subtype,
                json.dumps(payload, ensure_ascii=False),
                answer,
                now,
                tokens[0],
                tokens[1],
                price_stars,
                1 if is_favorite else 0,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_history(user_id: int, limit: int = 5) -> List[sqlite3.Row]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return cur.fetchall()


def save_draft(user_id: int, mode: str, subtype: str, payload: Dict[str, Any]) -> int:
    now = int(time.time())
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO drafts (user_id, mode, subtype, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, mode, subtype, json.dumps(payload, ensure_ascii=False), now),
        )
        conn.commit()
        return int(cur.lastrowid)


def pop_draft(draft_id: int) -> Dict[str, Any] | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = cur.fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
        conn.commit()
    try:
        return json.loads(row["payload_json"])
    except Exception:  # noqa: BLE001
        return None


def mark_favorite(history_id: int, value: bool = True) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE history SET is_favorite = ? WHERE id = ?",
            (1 if value else 0, history_id),
        )
        conn.commit()

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    Path(config.DATA_DIR).mkdir(exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                free_ai_left INTEGER DEFAULT ?,
                paid_credits INTEGER DEFAULT 0,
                sub_until INTEGER,
                created_at INTEGER,
                profile_json TEXT DEFAULT '{}'
            )
            """,
            (config.DEFAULT_FREE_REQUESTS,),
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                module TEXT,
                subtype TEXT,
                input_json TEXT,
                result_text TEXT,
                created_at INTEGER,
                is_favorite INTEGER DEFAULT 0,
                price_stars INTEGER DEFAULT 0,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def get_user(tg_id: int) -> sqlite3.Row:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()
        if row:
            return row
        now = int(time.time())
        conn.execute(
            "INSERT INTO users (tg_id, free_ai_left, paid_credits, created_at) VALUES (?, ?, 0, ?)",
            (tg_id, config.DEFAULT_FREE_REQUESTS, now),
        )
        conn.commit()
        return get_user(tg_id)


def update_profile(tg_id: int, profile: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute("UPDATE users SET profile_json = ? WHERE tg_id = ?", (json.dumps(profile), tg_id))
        conn.commit()


def get_profile(tg_id: int) -> Dict[str, Any]:
    row = get_user(tg_id)
    raw = row["profile_json"] or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def reset_profile(tg_id: int) -> None:
    update_profile(tg_id, {})


def decrement_free(tg_id: int) -> int:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET free_ai_left = CASE WHEN free_ai_left > 0 THEN free_ai_left - 1 ELSE 0 END WHERE tg_id = ?",
            (tg_id,),
        )
        cur = conn.execute("SELECT free_ai_left FROM users WHERE tg_id = ?", (tg_id,))
        val = cur.fetchone()[0]
        conn.commit()
        return val


def spend_paid_credit(tg_id: int) -> int:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET paid_credits = CASE WHEN paid_credits > 0 THEN paid_credits - 1 ELSE 0 END WHERE tg_id = ?",
            (tg_id,),
        )
        cur = conn.execute("SELECT paid_credits FROM users WHERE tg_id = ?", (tg_id,))
        val = cur.fetchone()[0]
        conn.commit()
        return val


def add_paid_credit(tg_id: int, count: int = 1) -> None:
    with _connect() as conn:
        conn.execute("UPDATE users SET paid_credits = paid_credits + ? WHERE tg_id = ?", (count, tg_id))
        conn.commit()


def grant_subscription(tg_id: int, until_ts: int) -> None:
    with _connect() as conn:
        conn.execute("UPDATE users SET sub_until = ? WHERE tg_id = ?", (until_ts, tg_id))
        conn.commit()


def has_subscription(row: sqlite3.Row) -> bool:
    sub_until = row["sub_until"] or 0
    return bool(sub_until and int(sub_until) > int(time.time()))


def save_history(
    tg_id: int,
    module: str,
    subtype: str,
    inputs: Dict[str, Any],
    result_text: str,
    price_stars: int,
    tokens_in: int,
    tokens_out: int,
) -> int:
    now = int(time.time())
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO history (tg_id, module, subtype, input_json, result_text, created_at, price_stars, tokens_in, tokens_out)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tg_id, module, subtype, json.dumps(inputs, ensure_ascii=False), result_text, now, price_stars, tokens_in, tokens_out),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_history(tg_id: int, limit: int = 5, offset: int = 0) -> list[sqlite3.Row]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM history WHERE tg_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (tg_id, limit, offset),
        )
        return cur.fetchall()


def toggle_favorite(history_id: int, value: bool) -> None:
    with _connect() as conn:
        conn.execute("UPDATE history SET is_favorite = ? WHERE id = ?", (1 if value else 0, history_id))
        conn.commit()

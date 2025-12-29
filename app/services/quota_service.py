from __future__ import annotations

import logging

from app.db.storage import Database

logger = logging.getLogger(__name__)


class QuotaService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def ensure_user(self, telegram_id: int) -> None:
        async with self.db.connect() as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, created_at) VALUES (?, datetime('now'))",
                (telegram_id,),
            )
            await conn.execute(
                "INSERT OR IGNORE INTO quotas (telegram_id, free_left, updated_at) VALUES (?, 3, datetime('now'))",
                (telegram_id,),
            )
            await conn.commit()

    async def get_free_left(self, telegram_id: int) -> int:
        await self.ensure_user(telegram_id)
        row = await self.db.fetchone("SELECT free_left FROM quotas WHERE telegram_id = ?", (telegram_id,))
        return int(row["free_left"]) if row else 0

    async def consume_one(self, telegram_id: int) -> bool:
        async with self.db.connect() as conn:
            await conn.execute("BEGIN")
            await conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, created_at) VALUES (?, datetime('now'))",
                (telegram_id,),
            )
            await conn.execute(
                "INSERT OR IGNORE INTO quotas (telegram_id, free_left, updated_at) VALUES (?, 3, datetime('now'))",
                (telegram_id,),
            )
            cursor = await conn.execute("SELECT free_left FROM quotas WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            if not row or int(row["free_left"]) <= 0:
                await conn.execute("ROLLBACK")
                return False
            await conn.execute(
                "UPDATE quotas SET free_left = free_left - 1, updated_at = datetime('now') WHERE telegram_id = ?",
                (telegram_id,),
            )
            await conn.commit()
            return True

    async def refund_one(self, telegram_id: int) -> None:
        await self.db.execute(
            "UPDATE quotas SET free_left = free_left + 1, updated_at = datetime('now') WHERE telegram_id = ?",
            (telegram_id,),
        )

    async def log_request(self, telegram_id: int, module: str, action: str, prompt_hash: str) -> None:
        await self.db.execute(
            "INSERT INTO requests_log (telegram_id, module, action, prompt_hash, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (telegram_id, module, action, prompt_hash),
        )

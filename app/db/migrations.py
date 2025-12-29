from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


async def apply_migrations(db_path: str) -> None:
    sql_path = Path(__file__).with_name("models.sql")
    sql_content = sql_path.read_text(encoding="utf-8")

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(sql_content)
        await db.commit()
        logger.info("Migrations applied")

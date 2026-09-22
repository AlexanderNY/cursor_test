"""Пул PostgreSQL для resume-api (общий db_9to18)."""
from __future__ import annotations

import logging
import re
from typing import Optional

import aiopg

from config import settings

logger = logging.getLogger(__name__)

_pool: Optional[aiopg.Pool] = None
_CLIENT_ENC_RE = re.compile(r"(?i)\bclient_encoding\s*=")


def normalize_pg_dsn(dsn: str) -> str:
    text = dsn.strip()
    if not text:
        return text
    if _CLIENT_ENC_RE.search(text):
        return text
    return f"{text} client_encoding=UTF8"


async def init_db(table_sql: list[str]) -> None:
    global _pool
    if _pool is not None:
        return
    dsn = normalize_pg_dsn((settings.DATABASE_URL or "").strip())
    if not dsn:
        raise RuntimeError("DATABASE_URL is required")
    _pool = await aiopg.create_pool(
        dsn,
        minsize=max(1, settings.DB_POOL_MINSIZE),
        maxsize=max(settings.DB_POOL_MINSIZE, settings.DB_POOL_MAXSIZE),
        timeout=30,
    )
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            for sql in table_sql:
                await cur.execute(sql)


async def get_db_connection() -> aiopg.Connection:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return await _pool.acquire()


async def release_db_connection(conn: aiopg.Connection) -> None:
    if _pool is None:
        return
    _pool.release(conn)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

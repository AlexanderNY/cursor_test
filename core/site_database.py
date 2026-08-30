"""Отдельный пул PostgreSQL для контура 9to18.ru (db_9to18)."""
from __future__ import annotations

import re
from typing import Optional

import aiopg

from config import settings

_pool: Optional[aiopg.Pool] = None


def resolve_site_database_url() -> str:
    """DSN для сайта: SITE_DATABASE_URL или тот же хост с dbname=db_9to18."""
    explicit = (settings.SITE_DATABASE_URL or "").strip()
    if explicit:
        return explicit
    base = (settings.DATABASE_URL or "").strip()
    if not base:
        raise RuntimeError("SITE_DATABASE_URL or DATABASE_URL is required for site DB")
    if re.search(r"(?i)\bdbname\s*=", base):
        return re.sub(r"(?i)\bdbname\s*=\s*\S+", "dbname=db_9to18", base, count=1)
    return f"{base} dbname=db_9to18"


async def init_site_db(table_sql: list[str]) -> None:
    global _pool
    if _pool is not None:
        return
    dsn = resolve_site_database_url()
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


async def get_site_db_connection() -> aiopg.Connection:
    if _pool is None:
        raise RuntimeError("Site database pool is not initialized")
    return await _pool.acquire()


async def release_site_db_connection(conn: aiopg.Connection) -> None:
    if _pool is None:
        return
    _pool.release(conn)


async def close_site_db() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

"""Пул PostgreSQL для site-api (db_9to18)."""
from __future__ import annotations

import aiopg

from config import settings
from shared.pg_pool import AsyncPgPool, normalize_pg_dsn

_pool = AsyncPgPool(ensure_database=True)


def resolve_database_url() -> str:
    dsn = (settings.DATABASE_URL or "").strip()
    if not dsn:
        raise RuntimeError("DATABASE_URL is required")
    return normalize_pg_dsn(dsn)


async def init_db(table_sql: list[str]) -> None:
    await _pool.init(
        settings.DATABASE_URL,
        table_sql,
        minsize=settings.DB_POOL_MINSIZE,
        maxsize=settings.DB_POOL_MAXSIZE,
    )


async def get_db_connection() -> aiopg.Connection:
    return await _pool.acquire()


async def release_db_connection(conn: aiopg.Connection) -> None:
    _pool.release(conn)


# Aliases for code ported from core site_* names
get_site_db_connection = get_db_connection
release_site_db_connection = release_db_connection


async def close_db() -> None:
    await _pool.close()

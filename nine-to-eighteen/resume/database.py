"""Пул PostgreSQL для resume-api (общий db_9to18)."""
from __future__ import annotations

import aiopg

from config import settings
from shared.pg_pool import AsyncPgPool

_pool = AsyncPgPool(ensure_database=False)


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


async def close_db() -> None:
    await _pool.close()

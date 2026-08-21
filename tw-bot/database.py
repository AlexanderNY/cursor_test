"""Подключение к базе данных."""

import aiopg
from typing import Optional

from config import settings
from models import ALL_TABLES

_pool: Optional[aiopg.Pool] = None


async def init_db(tables: list | None = None) -> None:
    """Инициализация пула и создание таблиц tw-bot."""
    global _pool
    if _pool is None:
        _pool = await aiopg.create_pool(
            settings.DATABASE_URL,
            minsize=max(1, int(getattr(settings, "DB_POOL_MINSIZE", 2))),
            maxsize=max(1, int(getattr(settings, "DB_POOL_MAXSIZE", 8))),
            timeout=30,
        )
        ddl = tables if tables is not None else ALL_TABLES
        if ddl:
            async with _pool.acquire() as conn:
                async with conn.cursor() as cur:
                    for table_sql in ddl:
                        await cur.execute(table_sql)


async def get_db_connection() -> aiopg.Connection:
    if _pool is None:
        await init_db()
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

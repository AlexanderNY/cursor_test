"""Подключение к базе данных PostgreSQL."""

import aiopg
from typing import Optional
from config import settings
from models import ALL_TABLES


_pool: Optional[aiopg.Pool] = None


async def init_db() -> None:
    """Инициализация пула соединений и создание таблиц wp-bot."""
    global _pool

    if _pool is None:
        _pool = await aiopg.create_pool(
            settings.DATABASE_URL,
            minsize=1,
            maxsize=10,
            timeout=30,
        )
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                for table_sql in ALL_TABLES:
                    await cur.execute(table_sql)


async def get_db_connection() -> aiopg.Connection:
    """Получение соединения с базой данных из пула."""
    if _pool is None:
        await init_db()

    if _pool is None:
        raise RuntimeError("Database pool is not initialized")

    return await _pool.acquire()


async def release_db_connection(conn: aiopg.Connection) -> None:
    """Возврат соединения в пул."""
    if _pool is None:
        return

    _pool.release(conn)


async def close_db() -> None:
    """Закрытие пула соединений."""
    global _pool

    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

"""Подключение к базе данных (таблицы threads_* создаются в core)."""

import aiopg
from typing import Optional

from config import settings

_pool: Optional[aiopg.Pool] = None


async def init_db() -> None:
    """Инициализация пула соединений с базой данных."""
    global _pool
    if _pool is None:
        _pool = await aiopg.create_pool(
            settings.DATABASE_URL,
            minsize=1,
            maxsize=10,
            timeout=30,
        )


async def get_db_connection() -> aiopg.Connection:
    """Получение соединения из пула."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return await _pool.acquire()


def release_db_connection(conn: aiopg.Connection) -> None:
    """Возврат соединения в пул."""
    if _pool is not None:
        _pool.release(conn)


async def close_db() -> None:
    """Закрытие пула соединений."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

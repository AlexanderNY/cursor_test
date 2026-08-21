"""Подключение к БД Processor."""

from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager

import aiopg

from config import settings

_pool: Optional[aiopg.Pool] = None


async def init_db() -> None:
    """Инициализация пула соединений (схема создаётся сервисом core)."""
    global _pool
    if _pool is not None:
        return

    _pool = await aiopg.create_pool(
        settings.DATABASE_URL,
        minsize=max(1, int(getattr(settings, "DB_POOL_MINSIZE", 2))),
        maxsize=max(1, int(getattr(settings, "DB_POOL_MAXSIZE", 8))),
        timeout=30,
    )


@asynccontextmanager
async def get_db_connection() -> AsyncIterator[aiopg.Connection]:
    """Получение соединения с базой данных из пула (контекстный менеджер)."""
    if _pool is None:
        await init_db()

    if _pool is None:
        raise RuntimeError("Database pool is not initialized")

    async with _pool.acquire() as conn:
        yield conn


async def close_db() -> None:
    """Закрытие пула соединений."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

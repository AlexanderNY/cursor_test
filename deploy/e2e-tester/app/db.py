from __future__ import annotations

import logging
from typing import Any

import aiopg
from psycopg2.extras import RealDictCursor

from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: aiopg.Pool | None = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS credentials (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    cred_type TEXT NOT NULL CHECK (cred_type IN ('password', 'jwt')),
    payload_encrypted TEXT NOT NULL,
    meta TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenarios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('yaml', 'json', 'playwright_py')),
    source TEXT NOT NULL,
    credentials_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    credentials_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'passed', 'failed')),
    error_summary TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS run_events (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level TEXT NOT NULL DEFAULT 'info',
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('screenshot', 'trace')),
    path TEXT NOT NULL,
    step_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_run_events_run_id ON run_events(run_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);
"""


async def init_pool() -> aiopg.Pool:
    global _pool
    settings = get_settings()
    if _pool is None:
        _pool = await aiopg.create_pool(
            dsn=settings.DATABASE_URL,
            minsize=settings.DB_POOL_MINSIZE,
            maxsize=settings.DB_POOL_MAXSIZE,
        )
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SCHEMA_SQL)
        logger.info("tester DB schema ready")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def get_pool() -> aiopg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool is not initialized")
    return _pool


async def fetch_one(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(cursor_factory=RealDictCursor) as cur:
            await cur.execute(sql, params)
            row = await cur.fetchone()
            return dict(row) if row else None


async def fetch_all(sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(cursor_factory=RealDictCursor) as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def execute(sql: str, params: tuple[Any, ...] | None = None) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)


async def execute_returning(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(cursor_factory=RealDictCursor) as cur:
            await cur.execute(sql, params)
            row = await cur.fetchone()
            if row is None:
                raise RuntimeError("expected RETURNING row")
            return dict(row)

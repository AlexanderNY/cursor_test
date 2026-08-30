from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

from app.config import get_settings

logger = logging.getLogger(__name__)

_db_path: Path | None = None
_lock = asyncio.Lock()
_initialized = False

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    cred_type TEXT NOT NULL CHECK (cred_type IN ('password', 'jwt')),
    payload_encrypted TEXT NOT NULL,
    meta TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    meta TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('yaml', 'json', 'playwright_py')),
    source TEXT NOT NULL,
    credentials_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    site_id INTEGER REFERENCES sites(id) ON DELETE SET NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    credentials_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    site_id INTEGER REFERENCES sites(id) ON DELETE SET NULL,
    base_url_snapshot TEXT,
    summary_json TEXT,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'passed', 'failed')),
    error_summary TEXT,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS run_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    level TEXT NOT NULL DEFAULT 'info',
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES run_results(id) ON DELETE CASCADE,
    node_type TEXT NOT NULL CHECK (node_type IN ('section', 'subsection', 'action')),
    key TEXT,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'passed'
        CHECK (status IN ('passed', 'failed', 'skipped')),
    error TEXT,
    started_at TEXT,
    finished_at TEXT,
    duration_ms INTEGER,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    result_id INTEGER REFERENCES run_results(id) ON DELETE SET NULL,
    kind TEXT NOT NULL CHECK (kind IN ('screenshot', 'trace')),
    path TEXT NOT NULL,
    step_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER REFERENCES sites(id) ON DELETE SET NULL,
    credentials_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    base_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    max_pages INTEGER NOT NULL DEFAULT 40,
    max_depth INTEGER NOT NULL DEFAULT 3,
    same_origin_only INTEGER NOT NULL DEFAULT 1,
    do_login INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT,
    summary_json TEXT,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS discovery_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discovery_id INTEGER NOT NULL REFERENCES discoveries(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('link', 'button', 'input', 'nav')),
    page_url TEXT,
    page_path TEXT,
    href TEXT,
    path TEXT,
    label TEXT,
    selector TEXT,
    text TEXT,
    interactive INTEGER NOT NULL DEFAULT 1,
    selected INTEGER NOT NULL DEFAULT 0,
    meta TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_run_events_run_id ON run_events(run_id);
CREATE INDEX IF NOT EXISTS idx_run_results_run_id ON run_results(run_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_discoveries_status ON discoveries(status);
CREATE INDEX IF NOT EXISTS idx_discovery_items_discovery_id ON discovery_items(discovery_id);
"""

DEFAULT_COPYPARSE_META = {
    "login": {
        "path": "/sign-in",
        "username_selector": 'input[placeholder="Enter your username"]',
        "password_selector": 'input[type="password"]',
        "submit_selector": 'button[type="submit"]',
    },
    "notes": "Public CopyParse SaaS UI",
}

_DATETIME_KEYS = frozenset(
    {
        "created_at",
        "started_at",
        "finished_at",
        "ts",
    }
)
_BOOL_KEYS = frozenset(
    {
        "same_origin_only",
        "do_login",
        "interactive",
        "selected",
    }
)


def _adapt_sql(sql: str) -> str:
    """Postgres-style %s / NOW() → SQLite."""
    out = sql.replace("NOW()", "datetime('now')")
    # boolean literals in UPDATE/WHERE
    out = re.sub(r"\bTRUE\b", "1", out)
    out = re.sub(r"\bFALSE\b", "0", out)
    out = out.replace("%s", "?")
    return out


def _parse_dt(value: Any) -> Any:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            # SQLite datetime('now') → 'YYYY-MM-DD HH:MM:SS'
            return datetime.fromisoformat(value.replace(" ", "T", 1))
        except ValueError:
            return value
    return value


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    data = dict(row)
    for key in _DATETIME_KEYS:
        if key in data:
            data[key] = _parse_dt(data[key])
    for key in _BOOL_KEYS:
        if key in data and data[key] is not None:
            data[key] = bool(data[key])
    return data


async def _connect() -> aiosqlite.Connection:
    if _db_path is None:
        raise RuntimeError("DB is not initialized")
    conn = await aiosqlite.connect(str(_db_path))
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("PRAGMA journal_mode = WAL")
    return conn


async def _seed_default_sites() -> None:
    existing = await fetch_one("SELECT id FROM sites WHERE name = %s", ("copyparse",))
    if existing is not None:
        return
    await execute(
        """
        INSERT INTO sites (name, base_url, meta)
        VALUES (%s, %s, %s)
        ON CONFLICT(name) DO NOTHING
        """,
        (
            "copyparse",
            "https://www.copyparse.ru",
            json.dumps(DEFAULT_COPYPARSE_META, ensure_ascii=False),
        ),
    )
    logger.info("seeded default site: copyparse → https://www.copyparse.ru")


async def init_pool() -> None:
    """Open/create SQLite DB under DATA_DIR (single-file, no Postgres)."""
    global _db_path, _initialized
    settings = get_settings()
    path = settings.sqlite_path
    path.parent.mkdir(parents=True, exist_ok=True)
    _db_path = path
    async with _lock:
        conn = await _connect()
        try:
            await conn.executescript(SCHEMA_SQL)
            await conn.commit()
        finally:
            await conn.close()
    _initialized = True
    logger.info("tester SQLite ready at %s", path)
    await _seed_default_sites()


async def close_pool() -> None:
    global _initialized
    _initialized = False


def get_pool() -> None:
    """Compatibility shim — SQLite has no pool."""
    if not _initialized or _db_path is None:
        raise RuntimeError("DB is not initialized")
    return None


async def fetch_one(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    if not _initialized:
        raise RuntimeError("DB is not initialized")
    q = _adapt_sql(sql)
    async with _lock:
        conn = await _connect()
        try:
            cur = await conn.execute(q, params or ())
            row = await cur.fetchone()
            return _row_to_dict(row) if row else None
        finally:
            await conn.close()


async def fetch_all(sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    if not _initialized:
        raise RuntimeError("DB is not initialized")
    q = _adapt_sql(sql)
    async with _lock:
        conn = await _connect()
        try:
            cur = await conn.execute(q, params or ())
            rows = await cur.fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            await conn.close()


async def execute(sql: str, params: tuple[Any, ...] | None = None) -> None:
    if not _initialized:
        raise RuntimeError("DB is not initialized")
    q = _adapt_sql(sql)
    async with _lock:
        conn = await _connect()
        try:
            await conn.execute(q, params or ())
            await conn.commit()
        finally:
            await conn.close()


async def execute_returning(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
    if not _initialized:
        raise RuntimeError("DB is not initialized")
    q = _adapt_sql(sql)
    async with _lock:
        conn = await _connect()
        try:
            cur = await conn.execute(q, params or ())
            row = await cur.fetchone()
            await conn.commit()
            if row is None:
                raise RuntimeError("expected RETURNING row")
            return _row_to_dict(row)
        finally:
            await conn.close()

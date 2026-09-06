"""Отдельный пул PostgreSQL для контура 9to18.ru (db_9to18)."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

import aiopg
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import settings

logger = logging.getLogger(__name__)

_pool: Optional[aiopg.Pool] = None

DEFAULT_SITE_DBNAME = "db_9to18"
_DBNAME_VALUE_RE = re.compile(r"(?i)\bdbname\s*=\s*(\S+)")
_DBNAME_ASSIGN_RE = re.compile(r"(?i)\bdbname\s*=\s*\S+")
_CLIENT_ENC_RE = re.compile(r"(?i)\bclient_encoding\s*=")
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def extract_dbname(dsn: str) -> Optional[str]:
    match = _DBNAME_VALUE_RE.search(dsn)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def replace_dbname(dsn: str, dbname: str) -> str:
    if not _SAFE_IDENT_RE.fullmatch(dbname):
        raise ValueError(f"Unsafe database name: {dbname!r}")
    if _DBNAME_ASSIGN_RE.search(dsn):
        return _DBNAME_ASSIGN_RE.sub(f"dbname={dbname}", dsn, count=1)
    return f"{dsn} dbname={dbname}"


def normalize_pg_dsn(dsn: str) -> str:
    """Force UTF-8 client encoding.

    Windows PostgreSQL often has lc_messages=Russian_Russia.1251. A FATAL
    (e.g. missing database) then arrives in CP1251, aiopg raises
    UnicodeDecodeError in a callback, and startup hangs until TimeoutError.
    """
    text = dsn.strip()
    if not text:
        return text
    if _CLIENT_ENC_RE.search(text):
        return text
    return f"{text} client_encoding=UTF8"


def resolve_site_database_url() -> str:
    """DSN для сайта: SITE_DATABASE_URL или тот же хост с dbname=db_9to18."""
    explicit = (settings.SITE_DATABASE_URL or "").strip()
    if explicit:
        return normalize_pg_dsn(explicit)
    base = (settings.DATABASE_URL or "").strip()
    if not base:
        raise RuntimeError("SITE_DATABASE_URL or DATABASE_URL is required for site DB")
    return normalize_pg_dsn(replace_dbname(base, DEFAULT_SITE_DBNAME))


def _ensure_database_exists_sync(admin_dsn: str, dbname: str) -> None:
    """CREATE DATABASE cannot run on an aiopg async connection."""
    if not _SAFE_IDENT_RE.fullmatch(dbname):
        raise RuntimeError(f"Unsafe site database name: {dbname!r}")
    conn = psycopg2.connect(admin_dsn, connect_timeout=15)
    try:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone():
                return
            logger.warning("Site database %s is missing; creating it", dbname)
            cur.execute(f"CREATE DATABASE {dbname} ENCODING 'UTF8'")
    finally:
        conn.close()


async def _ensure_database_exists(site_dsn: str) -> None:
    """Create db_9to18 via an already-working DB (db_bot / postgres) if missing."""
    dbname = extract_dbname(site_dsn) or DEFAULT_SITE_DBNAME
    admin_base = (settings.DATABASE_URL or "").strip() or replace_dbname(
        site_dsn, "postgres"
    )
    admin_dsn = normalize_pg_dsn(admin_base)
    await asyncio.to_thread(_ensure_database_exists_sync, admin_dsn, dbname)


async def init_site_db(table_sql: list[str]) -> None:
    global _pool
    if _pool is not None:
        return
    dsn = resolve_site_database_url()
    await _ensure_database_exists(dsn)
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

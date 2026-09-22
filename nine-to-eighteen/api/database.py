"""Пул PostgreSQL для 9to18 (только db_9to18)."""
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

DEFAULT_DBNAME = "db_9to18"
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
    text = dsn.strip()
    if not text:
        return text
    if _CLIENT_ENC_RE.search(text):
        return text
    return f"{text} client_encoding=UTF8"


def resolve_database_url() -> str:
    dsn = (settings.DATABASE_URL or "").strip()
    if not dsn:
        raise RuntimeError("DATABASE_URL is required")
    return normalize_pg_dsn(dsn)


def _ensure_database_exists_sync(admin_dsn: str, dbname: str) -> None:
    if not _SAFE_IDENT_RE.fullmatch(dbname):
        raise RuntimeError(f"Unsafe database name: {dbname!r}")
    conn = psycopg2.connect(admin_dsn, connect_timeout=15)
    try:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone():
                return
            logger.warning("Database %s is missing; creating it", dbname)
            cur.execute(f"CREATE DATABASE {dbname} ENCODING 'UTF8'")
    finally:
        conn.close()


async def _ensure_database_exists(dsn: str) -> None:
    dbname = extract_dbname(dsn) or DEFAULT_DBNAME
    admin_dsn = normalize_pg_dsn(replace_dbname(dsn, "postgres"))
    await asyncio.to_thread(_ensure_database_exists_sync, admin_dsn, dbname)


async def init_db(table_sql: list[str]) -> None:
    global _pool
    if _pool is not None:
        return
    dsn = resolve_database_url()
    try:
        await _ensure_database_exists(dsn)
    except Exception:
        logger.exception("Could not auto-create database; continuing with connect")
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


async def get_db_connection() -> aiopg.Connection:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return await _pool.acquire()


async def release_db_connection(conn: aiopg.Connection) -> None:
    if _pool is None:
        return
    _pool.release(conn)


# Aliases for code ported from core site_* names
get_site_db_connection = get_db_connection
release_site_db_connection = release_db_connection


async def close_db() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

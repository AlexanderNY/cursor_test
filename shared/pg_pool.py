"""Reusable aiopg pool + PostgreSQL DSN helpers."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

import aiopg
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)

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


def ensure_database_exists_sync(admin_dsn: str, dbname: str) -> None:
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


async def ensure_database_exists(
    dsn: str,
    *,
    default_dbname: str = DEFAULT_DBNAME,
) -> None:
    dbname = extract_dbname(dsn) or default_dbname
    admin_dsn = normalize_pg_dsn(replace_dbname(dsn, "postgres"))
    await asyncio.to_thread(ensure_database_exists_sync, admin_dsn, dbname)


class AsyncPgPool:
    """One aiopg pool per service process; DSN and sizes come from the caller."""

    def __init__(
        self,
        *,
        default_dbname: str = DEFAULT_DBNAME,
        ensure_database: bool = False,
        pool_timeout: float = 30,
    ) -> None:
        self._pool: Optional[aiopg.Pool] = None
        self.default_dbname = default_dbname
        self.ensure_database = ensure_database
        self.pool_timeout = pool_timeout

    async def init(
        self,
        dsn: str,
        table_sql: list[str],
        *,
        minsize: int,
        maxsize: int,
    ) -> None:
        if self._pool is not None:
            return
        normalized = normalize_pg_dsn((dsn or "").strip())
        if not normalized:
            raise RuntimeError("DATABASE_URL is required")
        if self.ensure_database:
            try:
                await ensure_database_exists(
                    normalized,
                    default_dbname=self.default_dbname,
                )
            except Exception:
                logger.exception("Could not auto-create database; continuing with connect")
        self._pool = await aiopg.create_pool(
            normalized,
            minsize=max(1, minsize),
            maxsize=max(minsize, maxsize),
            timeout=self.pool_timeout,
        )
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                for sql in table_sql:
                    await cur.execute(sql)

    async def acquire(self) -> aiopg.Connection:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        return await self._pool.acquire()

    def release(self, conn: aiopg.Connection) -> None:
        if self._pool is None:
            return
        self._pool.release(conn)

    async def close(self) -> None:
        if self._pool is None:
            return
        self._pool.close()
        await self._pool.wait_closed()
        self._pool = None

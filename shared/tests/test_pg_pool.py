"""Unit tests for shared.pg_pool DSN helpers."""
from __future__ import annotations

import pytest

from shared.pg_pool import (
    ensure_database_exists_sync,
    extract_dbname,
    normalize_pg_dsn,
    replace_dbname,
)


def test_replace_dbname_swaps_existing() -> None:
    dsn = "dbname=db_bot user=postgres host=host.docker.internal"
    out = replace_dbname(dsn, "db_9to18")
    assert "dbname=db_9to18" in out
    assert "dbname=db_bot" not in out
    assert "user=postgres" in out


def test_replace_dbname_appends_when_missing() -> None:
    dsn = "user=postgres host=localhost"
    assert replace_dbname(dsn, "db_9to18") == "user=postgres host=localhost dbname=db_9to18"


def test_replace_dbname_rejects_unsafe() -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        replace_dbname("dbname=x", "db;drop")


def test_extract_dbname() -> None:
    assert extract_dbname("dbname=db_bot user=x") == "db_bot"
    assert extract_dbname("user=x host=localhost") is None


def test_normalize_pg_dsn_adds_utf8_once() -> None:
    dsn = "dbname=db_9to18 user=u host=localhost"
    once = normalize_pg_dsn(dsn)
    assert "client_encoding=UTF8" in once
    twice = normalize_pg_dsn(once)
    assert twice.count("client_encoding=UTF8") == 1


def test_ensure_database_exists_sync_rejects_unsafe_name() -> None:
    with pytest.raises(RuntimeError, match="Unsafe"):
        ensure_database_exists_sync("dbname=postgres", "db;drop")

"""Unit tests for site database DSN helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

CORE_DIR = Path(__file__).resolve().parents[1]

_config = ModuleType("config")
_config.settings = SimpleNamespace(
    DATABASE_URL="dbname=db_bot user=u password=p host=localhost",
    SITE_DATABASE_URL="",
    DB_POOL_MINSIZE=2,
  DB_POOL_MAXSIZE=8,
)
sys.modules["config"] = _config

_SPEC = importlib.util.spec_from_file_location(
    "site_database",
    CORE_DIR / "site_database.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["site_database"] = _mod
_SPEC.loader.exec_module(_mod)

extract_dbname = _mod.extract_dbname
normalize_pg_dsn = _mod.normalize_pg_dsn
replace_dbname = _mod.replace_dbname
resolve_site_database_url = _mod.resolve_site_database_url


def test_replace_dbname_swaps_existing() -> None:
    dsn = "dbname=db_bot user=postgres host=host.docker.internal"
    out = replace_dbname(dsn, "db_9to18")
    assert "dbname=db_9to18" in out
    assert "dbname=db_bot" not in out
    assert "user=postgres" in out


def test_replace_dbname_appends_when_missing() -> None:
    dsn = "user=postgres host=localhost"
    assert replace_dbname(dsn, "db_9to18") == "user=postgres host=localhost dbname=db_9to18"


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
        _mod._ensure_database_exists_sync("dbname=postgres", "db;drop")


def test_resolve_site_database_url_rewrites_main_dsn(monkeypatch) -> None:
    monkeypatch.setattr(
        _mod.settings,
        "DATABASE_URL",
        "dbname=db_bot user=postgres password=secret host=host.docker.internal",
    )
    monkeypatch.setattr(_mod.settings, "SITE_DATABASE_URL", "")
    dsn = resolve_site_database_url()
    assert "dbname=db_9to18" in dsn
    assert "dbname=db_bot" not in dsn
    assert "client_encoding=UTF8" in dsn
    assert "host=host.docker.internal" in dsn

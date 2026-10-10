"""Unit tests for site-api in-memory rate limiter."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "dbname=test user=test password=test host=127.0.0.1")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

_SPEC = importlib.util.spec_from_file_location("site_rate_limit", API_DIR / "rate_limit.py")
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["site_rate_limit"] = _mod
_SPEC.loader.exec_module(_mod)

check_rate_limit = _mod.check_rate_limit
reset_rate_limits_for_tests = _mod.reset_rate_limits_for_tests
client_key = _mod.client_key


@pytest.fixture(autouse=True)
def _clear():
    reset_rate_limits_for_tests()
    yield
    reset_rate_limits_for_tests()


def test_auth_bucket_allows_then_blocks():
    for _ in range(20):
        check_rate_limit("1.2.3.4", "auth", limit=20, window_sec=60)
    with pytest.raises(HTTPException) as exc:
        check_rate_limit("1.2.3.4", "auth", limit=20, window_sec=60)
    assert exc.value.status_code == 429


def test_buckets_are_independent():
    check_rate_limit("9.9.9.9", "auth", limit=1, window_sec=60)
    with pytest.raises(HTTPException):
        check_rate_limit("9.9.9.9", "auth", limit=1, window_sec=60)
    check_rate_limit("9.9.9.9", "contact", limit=1, window_sec=60)


def test_client_key_prefers_forwarded_for():
    request = SimpleNamespace(
        headers={"x-forwarded-for": "10.0.0.8, 10.0.0.1"},
        client=SimpleNamespace(host="127.0.0.1"),
    )
    assert client_key(request) == "10.0.0.8"

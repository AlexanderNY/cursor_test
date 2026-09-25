"""Unit tests for resume-api in-memory rate limiter."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("rate_limit", API_DIR / "rate_limit.py")
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["rate_limit"] = _mod
_SPEC.loader.exec_module(_mod)

check_rate_limit = _mod.check_rate_limit
enforce_rate_limit = _mod.enforce_rate_limit
reset_rate_limits_for_tests = _mod.reset_rate_limits_for_tests


@pytest.fixture(autouse=True)
def _clear_limits():
    reset_rate_limits_for_tests()
    yield
    reset_rate_limits_for_tests()


def test_allows_under_limit():
    for _ in range(3):
        info = check_rate_limit(1, "ai", limit=3, window_sec=60)
        assert info["remaining"] >= 0


def test_blocks_over_limit():
    for _ in range(2):
        check_rate_limit(42, "generate", limit=2, window_sec=60)
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(42, "generate", limit=2, window_sec=60)
    assert exc_info.value.status_code == 429
    assert exc_info.value.headers is not None
    assert exc_info.value.headers.get("X-RateLimit-Remaining") == "0"


def test_buckets_are_isolated():
    for _ in range(2):
        check_rate_limit(7, "ai", limit=2, window_sec=60)
    # preview bucket still free
    check_rate_limit(7, "preview", limit=2, window_sec=60)


def test_users_are_isolated():
    for _ in range(2):
        check_rate_limit(1, "export", limit=2, window_sec=60)
    check_rate_limit(2, "export", limit=2, window_sec=60)

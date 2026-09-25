"""Unit tests for Learn public posts TTL cache."""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "ttl_cache",
    API_DIR / "services" / "ttl_cache.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["ttl_cache"] = _mod
_SPEC.loader.exec_module(_mod)

TtlCache = _mod.TtlCache


def test_ttl_cache_get_set_and_deepcopy() -> None:
    cache = TtlCache(ttl_sec=60)
    payload = {"slug": "a", "tags": ["x"]}
    cache.set("post:a", payload)
    payload["tags"].append("mutated")

    cached = cache.get("post:a")
    assert cached == {"slug": "a", "tags": ["x"]}
    cached["tags"].append("caller")
    assert cache.get("post:a") == {"slug": "a", "tags": ["x"]}


def test_ttl_cache_expires() -> None:
    cache = TtlCache(ttl_sec=0.05)
    cache.set("list:published", [{"slug": "a"}])
    assert cache.get("list:published") == [{"slug": "a"}]
    time.sleep(0.06)
    assert cache.get("list:published") is None


def test_ttl_cache_clear() -> None:
    cache = TtlCache(ttl_sec=60)
    cache.set("post:a", {"slug": "a"})
    cache.clear()
    assert cache.get("post:a") is None

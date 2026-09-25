"""Unit tests for resume runtime settings merge/validate."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "runtime_settings",
    API_DIR / "services" / "runtime_settings.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["runtime_settings"] = _mod
_SPEC.loader.exec_module(_mod)

validate_and_normalize = _mod.validate_and_normalize
default_settings = _mod.default_settings
rate_limit_override = _mod.rate_limit_override
invalidate_cache = _mod.invalidate_cache


def test_defaults_have_buckets():
    doc = default_settings()
    assert doc["rateLimits"]["ai"]["requests"] == 8
    assert doc["features"]["exportEnabled"] is True


def test_merge_clamps_rate_limits():
    doc = validate_and_normalize(
        {"rateLimits": {"ai": {"requests": 99999, "windowSec": 0}}}
    )
    assert doc["rateLimits"]["ai"]["requests"] == 10_000
    assert doc["rateLimits"]["ai"]["windowSec"] == 1
    # untouched buckets stay default
    assert doc["rateLimits"]["export"]["requests"] == 10


def test_feature_flags_bool():
    doc = validate_and_normalize({"features": {"aiCoverLetter": 0, "exportEnabled": 1}})
    assert doc["features"]["aiCoverLetter"] is False
    assert doc["features"]["exportEnabled"] is True


def test_rate_limit_override_from_cache():
    invalidate_cache()
    assert rate_limit_override("ai") is None
    _mod._cache = validate_and_normalize(
        {"rateLimits": {"ai": {"requests": 3, "windowSec": 30}}}
    )
    assert rate_limit_override("ai") == (3, 30)
    invalidate_cache()

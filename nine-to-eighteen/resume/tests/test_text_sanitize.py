"""Unit tests for about text sanitization."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "text_sanitize",
    API_DIR / "services" / "text_sanitize.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["text_sanitize"] = _mod
_SPEC.loader.exec_module(_mod)

sanitize_plain_text = _mod.sanitize_plain_text


def test_strips_script_tags():
    out = sanitize_plain_text('<script>alert(1)</script>Привет')
    assert "<script>" not in out
    assert "alert(1)" in out
    assert "Привет" in out


def test_removes_null_and_controls():
    out = sanitize_plain_text("a\x00b\x07c\nd")
    assert "\x00" not in out
    assert "\x07" not in out
    assert "a" in out and "b" in out
    assert "\n" in out


def test_collapses_blank_lines():
    out = sanitize_plain_text("one\n\n\n\ntwo")
    assert out == "one\n\ntwo"


def test_truncates():
    out = sanitize_plain_text("x" * 9000, max_length=100)
    assert len(out) == 100

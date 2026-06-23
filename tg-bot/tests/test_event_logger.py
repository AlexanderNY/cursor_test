"""Tests for event_logger helpers."""

from services.event_logger import compute_text_hash, normalize_text, build_text_preview


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  Hello   WORLD  ") == "hello world"


def test_compute_text_hash_stable():
    h1 = compute_text_hash("Hello World")
    h2 = compute_text_hash("  hello   world  ")
    assert h1 == h2


def test_build_text_preview_truncates():
    text = "x" * 600
    preview = build_text_preview(text)
    assert len(preview) == 500

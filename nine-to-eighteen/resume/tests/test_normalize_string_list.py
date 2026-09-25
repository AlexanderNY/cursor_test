"""Unit tests for resume list normalization."""
from __future__ import annotations

from typing import Optional


def _normalize_string_list(values: Optional[list[str]], allowed: set[str]) -> list[str]:
    """Mirror of routers.resume._normalize_string_list (no FastAPI import)."""
    if values is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        key = str(raw or "").strip().lower()
        if key not in allowed or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def test_normalize_string_list_filters_and_dedupes() -> None:
    allowed = {"full", "part", "remote"}
    assert _normalize_string_list(
        [" Full ", "part", "full", "office", "", "REMOTE"],
        allowed,
    ) == ["full", "part", "remote"]


def test_normalize_string_list_none() -> None:
    assert _normalize_string_list(None, {"full"}) == []

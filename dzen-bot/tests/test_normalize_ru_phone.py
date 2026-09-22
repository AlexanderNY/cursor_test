"""Unit tests for dzen-bot phone normalization (no Selenium)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.phone_utils import PhoneNormalizeError, normalize_ru_phone  # noqa: E402


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("79001234567", "79001234567"),
        ("+79001234567", "79001234567"),
        ("8 900 123-45-67", "79001234567"),
        ("9001234567", "79001234567"),
        ("+7 (900) 123 45 67", "79001234567"),
    ],
)
def test_normalize_ru_phone_ok(raw: str, expected: str) -> None:
    assert normalize_ru_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "123",
        "123456789012",
        "abcdefghijk",
        "69001234567",
    ],
)
def test_normalize_ru_phone_invalid(raw: str) -> None:
    with pytest.raises(PhoneNormalizeError):
        normalize_ru_phone(raw)

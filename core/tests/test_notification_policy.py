"""Allowlist for clearing transient Telegram auth notifications."""

import pytest

from services.notification_policy import normalize_clear_types


def test_normalize_clear_types_dedupes_auth_types() -> None:
    assert normalize_clear_types(
        ["tg_auth_error", "tg_auth_error", "tg_auth_code", " tg_auth_2fa "]
    ) == ["tg_auth_error", "tg_auth_code", "tg_auth_2fa"]


def test_normalize_clear_types_rejects_general_and_empty() -> None:
    with pytest.raises(ValueError):
        normalize_clear_types(["general"])
    with pytest.raises(ValueError):
        normalize_clear_types([])

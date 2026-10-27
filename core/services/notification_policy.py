"""Rules for transient Telegram auth notifications."""

from __future__ import annotations

CLEARABLE_AUTH_TYPES = frozenset({"tg_auth_error", "tg_auth_code", "tg_auth_2fa"})
# A newer failure replaces the previous one so the inbox is not filled with copies.
REPLACED_ON_CREATE = frozenset({"tg_auth_error"})


def normalize_clear_types(types: list[str]) -> list[str]:
    """Return a deduped allowlist of auth notification types to delete.

    Raises:
        ValueError: types is empty or contains a type that must not be bulk-deleted.
    """
    if not types:
        raise ValueError("types must not be empty")

    normalized: list[str] = []
    for raw in types:
        item = (raw or "").strip()
        if item not in CLEARABLE_AUTH_TYPES:
            raise ValueError(f"unsupported notification type: {item or raw}")
        if item not in normalized:
            normalized.append(item)
    return normalized

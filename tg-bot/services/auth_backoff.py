"""Совместимый импорт. Реализация общая для ботов: shared.auth_backoff."""

from shared.auth_backoff import (
    AUTH_FAILURE_PAUSE_SEC,
    AuthAttemptBackoff,
    format_pause,
    next_attempt_suffix,
    pause_active_message,
    pause_seconds_for_failure,
)

__all__ = [
    "AUTH_FAILURE_PAUSE_SEC",
    "AuthAttemptBackoff",
    "format_pause",
    "next_attempt_suffix",
    "pause_active_message",
    "pause_seconds_for_failure",
]

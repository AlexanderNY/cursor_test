"""Пауза после неудачной попытки авторизации Telegram растёт и сбрасывается."""

from services.auth_backoff import (
    AUTH_FAILURE_PAUSE_SEC,
    AuthAttemptBackoff,
    format_pause,
    pause_seconds_for_failure,
)


def test_pause_schedule_grows_then_caps() -> None:
    assert AUTH_FAILURE_PAUSE_SEC == (300, 300, 600, 1200)
    assert pause_seconds_for_failure(1) == AUTH_FAILURE_PAUSE_SEC[0]
    assert pause_seconds_for_failure(2) == AUTH_FAILURE_PAUSE_SEC[1]
    assert pause_seconds_for_failure(3) == AUTH_FAILURE_PAUSE_SEC[2]
    assert pause_seconds_for_failure(4) == AUTH_FAILURE_PAUSE_SEC[-1]
    assert pause_seconds_for_failure(9) == AUTH_FAILURE_PAUSE_SEC[-1]
    assert pause_seconds_for_failure(0) == 0


def test_failure_blocks_until_pause_elapses_and_ignores_other_users() -> None:
    clock = {"now": 0.0}
    backoff = AuthAttemptBackoff(clock=lambda: clock["now"])

    assert backoff.retry_after_seconds(1) == 0
    pause = backoff.record_failure(1)
    assert pause == 300
    assert backoff.retry_after_seconds(1) == 300
    assert backoff.retry_after_seconds(2) == 0

    clock["now"] = 299
    assert backoff.retry_after_seconds(1) == 1
    clock["now"] = 300
    assert backoff.retry_after_seconds(1) == 0

    assert backoff.record_failure(1) == 300
    clock["now"] = 300 + 300
    assert backoff.record_failure(1) == 600


def test_flood_wait_extends_pause() -> None:
    backoff = AuthAttemptBackoff(clock=lambda: 0.0)
    assert backoff.record_failure(4, minimum_sec=5000) == 5000
    assert backoff.retry_after_seconds(4) == 5000


def test_success_resets_streak() -> None:
    clock = {"now": 0.0}
    backoff = AuthAttemptBackoff(clock=lambda: clock["now"])
    backoff.record_failure(5)
    backoff.record_failure(5)
    backoff.record_success(5)
    assert backoff.retry_after_seconds(5) == 0
    assert backoff.record_failure(5) == AUTH_FAILURE_PAUSE_SEC[0]


def test_format_pause() -> None:
    assert format_pause(45) == "45 с"
    assert format_pause(600) == "10 мин"
    assert format_pause(90) == "2 мин"

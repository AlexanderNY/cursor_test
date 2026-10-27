"""Пауза после неудачного входа: 5, 5, 10 и 20 минут."""

from shared.auth_backoff import (
    AUTH_FAILURE_PAUSE_SEC,
    AuthAttemptBackoff,
    format_pause,
    next_attempt_suffix,
    pause_active_message,
    pause_seconds_for_failure,
)


def test_pause_schedule_grows_then_caps() -> None:
    assert AUTH_FAILURE_PAUSE_SEC == (300, 300, 600, 1200)
    assert pause_seconds_for_failure(1) == 300
    assert pause_seconds_for_failure(2) == 300
    assert pause_seconds_for_failure(3) == 600
    assert pause_seconds_for_failure(4) == 1200
    assert pause_seconds_for_failure(9) == 1200
    assert pause_seconds_for_failure(0) == 0


def test_failure_blocks_until_pause_elapses_and_ignores_other_users() -> None:
    clock = {"now": 0.0}
    backoff = AuthAttemptBackoff(clock=lambda: clock["now"])

    assert backoff.retry_after_seconds(1) == 0
    assert backoff.record_failure(1) == 300
    assert backoff.retry_after_seconds(1) == 300
    assert backoff.retry_after_seconds(2) == 0

    clock["now"] = 299
    assert backoff.retry_after_seconds(1) == 1
    clock["now"] = 300
    assert backoff.retry_after_seconds(1) == 0

    assert backoff.record_failure(1) == 300
    clock["now"] = 600
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


def test_format_pause_and_user_messages() -> None:
    assert format_pause(45) == "45 с"
    assert format_pause(300) == "5 мин"
    assert pause_active_message(300) == "Пауза после неудачного входа. Повтор через 5 мин."
    assert next_attempt_suffix(600) == "Следующая попытка через 10 мин."

"""Повторный запрос кода Telegram не чаще одного раза в 120 секунд."""

from services.code_resend import (
    CODE_RESEND_INTERVAL_SEC,
    CodeResendLimiter,
    code_resend_retry_after_seconds,
)


def test_retry_after_is_zero_before_first_request():
    assert code_resend_retry_after_seconds(None, now=1000) == 0


def test_retry_after_blocks_until_interval_elapses():
    assert code_resend_retry_after_seconds(0, now=1, interval_sec=120) == 119
    assert code_resend_retry_after_seconds(0, now=119.2, interval_sec=120) == 1
    assert code_resend_retry_after_seconds(0, now=120, interval_sec=120) == 0
    assert code_resend_retry_after_seconds(0, now=121, interval_sec=120) == 0


def test_limiter_marks_user_and_ignores_other_users():
    clock = {"now": 0.0}
    limiter = CodeResendLimiter(interval_sec=CODE_RESEND_INTERVAL_SEC, clock=lambda: clock["now"])

    assert limiter.retry_after_seconds(7) == 0
    limiter.mark_sent(7)
    clock["now"] = 30
    assert limiter.retry_after_seconds(7) == 90
    assert limiter.retry_after_seconds(8) == 0

    clock["now"] = 120
    assert limiter.retry_after_seconds(7) == 0

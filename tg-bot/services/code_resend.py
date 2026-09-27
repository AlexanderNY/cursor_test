"""Ограничение повторного запроса кода авторизации Telegram."""

import math
import time
from typing import Callable, Dict, Optional


CODE_RESEND_INTERVAL_SEC = 120


def code_resend_retry_after_seconds(
    last_sent_at: Optional[float],
    now: float,
    interval_sec: int = CODE_RESEND_INTERVAL_SEC,
) -> int:
    """Сколько секунд ждать до следующего запроса кода.

    Args:
        last_sent_at: Момент предыдущего запроса (та же шкала, что и now).
        now: Текущий момент.
        interval_sec: Минимальный интервал между запросами.

    Returns:
        0, если запрос разрешён, иначе оставшиеся секунды (минимум 1).
    """
    if last_sent_at is None or interval_sec <= 0:
        return 0
    remaining = interval_sec - (now - last_sent_at)
    if remaining <= 0:
        return 0
    return max(1, math.ceil(remaining))


class CodeResendLimiter:
    """Память последних запросов кода по user_id."""

    def __init__(
        self,
        interval_sec: int = CODE_RESEND_INTERVAL_SEC,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._interval_sec = interval_sec
        self._clock = clock or time.monotonic
        self._last_sent_at: Dict[int, float] = {}

    def retry_after_seconds(self, user_id: int) -> int:
        """Оставшаяся пауза для пользователя."""
        return code_resend_retry_after_seconds(
            self._last_sent_at.get(user_id),
            self._clock(),
            self._interval_sec,
        )

    def mark_sent(self, user_id: int) -> None:
        """Фиксирует, что запрос кода к Telegram только что отправлен."""
        self._last_sent_at[user_id] = self._clock()

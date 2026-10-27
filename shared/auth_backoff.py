"""Пауза после неудачного входа в аккаунт площадки.

Серия быстрых попыток заканчивается таймаутом на стороне сервиса.
После каждой неудачи следующая попытка откладывается: 5, 5, 10 и 20 минут.
"""

import math
import time
from typing import Callable, Dict, Optional, Sequence


# 5, 5, 10 и 20 минут. Дальше пауза остаётся 20 минут.
AUTH_FAILURE_PAUSE_SEC: tuple[int, ...] = (300, 300, 600, 1200)


def pause_seconds_for_failure(
    failure_count: int,
    schedule: Sequence[int] = AUTH_FAILURE_PAUSE_SEC,
) -> int:
    """Длина паузы после failure_count-й неудачи (счёт с 1)."""
    if failure_count <= 0 or not schedule:
        return 0
    index = min(failure_count, len(schedule)) - 1
    return int(schedule[index])


def format_pause(seconds: int) -> str:
    """Короткий текст паузы для сообщения пользователю."""
    total = max(0, int(seconds))
    if total < 60:
        return f"{total} с"
    minutes = math.ceil(total / 60)
    return f"{minutes} мин"


def pause_active_message(seconds: int) -> str:
    """Текст, когда новую попытку входа делать ещё рано."""
    return f"Пауза после неудачного входа. Повтор через {format_pause(seconds)}."


def next_attempt_suffix(seconds: int) -> str:
    """Хвост к тексту ошибки после зафиксированной неудачи."""
    return f"Следующая попытка через {format_pause(seconds)}."


class AuthAttemptBackoff:
    """Память неудачных попыток входа по user_id. У каждого процесса свой экземпляр."""

    def __init__(
        self,
        schedule: Sequence[int] = AUTH_FAILURE_PAUSE_SEC,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._schedule = tuple(schedule)
        self._clock = clock or time.monotonic
        self._failures: Dict[int, int] = {}
        self._retry_at: Dict[int, float] = {}

    def retry_after_seconds(self, user_id: int) -> int:
        """Сколько секунд ещё нельзя входить. 0 — можно."""
        retry_at = self._retry_at.get(user_id)
        if retry_at is None:
            return 0
        remaining = retry_at - self._clock()
        if remaining <= 0:
            return 0
        return max(1, math.ceil(remaining))

    def record_failure(self, user_id: int, *, minimum_sec: int = 0) -> int:
        """Фиксирует неудачу и возвращает длину паузы в секундах.

        minimum_sec — нижняя граница, если площадка сама просит подождать дольше.
        """
        count = self._failures.get(user_id, 0) + 1
        self._failures[user_id] = count
        pause = max(
            pause_seconds_for_failure(count, self._schedule),
            max(0, int(minimum_sec)),
        )
        self._retry_at[user_id] = self._clock() + pause
        return pause

    def record_success(self, user_id: int) -> None:
        """Успешный вход сбрасывает серию неудач."""
        self._failures.pop(user_id, None)
        self._retry_at.pop(user_id, None)

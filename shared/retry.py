"""Async retry с экспоненциальным backoff для внешних API."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def default_attempts() -> int:
    return max(1, _env_int("RETRY_ATTEMPTS", 3))


def default_min_wait_sec() -> float:
    return max(0.0, _env_float("RETRY_MIN_WAIT_SEC", 0.5))


def default_max_wait_sec() -> float:
    return max(0.0, _env_float("RETRY_MAX_WAIT_SEC", 8.0))


def _wait_seconds(attempt_index: int, min_wait: float, max_wait: float) -> float:
    """attempt_index: 0 после первой неудачи → min_wait * 2^0."""
    return min(max_wait, min_wait * (2**attempt_index))


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    attempts: Optional[int] = None,
    min_wait_sec: Optional[float] = None,
    max_wait_sec: Optional[float] = None,
    retry_on: Optional[Callable[[BaseException], bool]] = None,
    operation_name: str = "operation",
) -> T:
    """Повторяет async-вызов при transient-ошибках с экспоненциальным backoff.

    Args:
        func: zero-arg async callable
        attempts: число попыток (default RETRY_ATTEMPTS=3)
        min_wait_sec / max_wait_sec: границы backoff
        retry_on: если False — сразу пробрасывает исключение без повтора
        operation_name: для логов
    """
    total = attempts if attempts is not None else default_attempts()
    min_wait = min_wait_sec if min_wait_sec is not None else default_min_wait_sec()
    max_wait = max_wait_sec if max_wait_sec is not None else default_max_wait_sec()
    should_retry = retry_on or (lambda _exc: True)

    last_error: Optional[BaseException] = None
    for attempt in range(total):
        try:
            return await func()
        except BaseException as exc:
            last_error = exc
            is_last = attempt >= total - 1
            if is_last or not should_retry(exc):
                raise
            wait = _wait_seconds(attempt, min_wait, max_wait)
            logger.warning(
                "%s failed (attempt %d/%d): %s; retry in %.2fs",
                operation_name,
                attempt + 1,
                total,
                exc,
                wait,
            )
            if wait > 0:
                await asyncio.sleep(wait)

    assert last_error is not None
    raise last_error

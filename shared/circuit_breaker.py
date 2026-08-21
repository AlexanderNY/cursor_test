"""Общий circuit breaker для внешних API (VK, Telegram, AI, …)."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Запрос заблокирован: circuit breaker открыт."""

    def __init__(self, name: str = "") -> None:
        self.name = name
        suffix = f" ({name})" if name else ""
        super().__init__(f"Circuit breaker is open{suffix}")


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


@dataclass
class CircuitBreaker:
    """Circuit breaker: closed → open после N failures → half_open после timeout."""

    name: str = ""
    failure_threshold: int = field(
        default_factory=lambda: _env_int("CIRCUIT_FAILURE_THRESHOLD", 5)
    )
    recovery_timeout_sec: float = field(
        default_factory=lambda: _env_float("CIRCUIT_RECOVERY_TIMEOUT_SEC", 60.0)
    )
    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED
    opened_at: Optional[float] = None

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if (
                self.opened_at is not None
                and time.monotonic() - self.opened_at >= self.recovery_timeout_sec
            ):
                self.state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit breaker %s half-open after %.0fs",
                    self.name or "?",
                    self.recovery_timeout_sec,
                )
                return True
            return False
        return True

    def is_open(self) -> bool:
        """True, если запросы сейчас блокируются (совместимость с ai_client)."""
        return not self.allow_request()

    def record_success(self) -> None:
        was_half_open = self.state == CircuitState.HALF_OPEN
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None
        if was_half_open:
            logger.info("Circuit breaker %s closed after probe success", self.name or "?")

    def record_failure(self) -> None:
        self.failure_count += 1
        if (
            self.state == CircuitState.HALF_OPEN
            or self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()
            logger.warning(
                "Circuit breaker %s opened after %d failures (threshold=%d)",
                self.name or "?",
                self.failure_count,
                self.failure_threshold,
            )

    def reset(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None


_registry: Dict[str, CircuitBreaker] = {}


def get_breaker(name: str, **kwargs: object) -> CircuitBreaker:
    """Возвращает singleton breaker по имени (vk_api, telegram, ai, …).

    kwargs передаются только при первом создании (threshold, recovery_timeout_sec).
    """
    if name not in _registry:
        _registry[name] = CircuitBreaker(name=name, **kwargs)  # type: ignore[arg-type]
    return _registry[name]


def reset_breaker_registry_for_tests() -> None:
    """Сброс реестра (только для тестов)."""
    _registry.clear()

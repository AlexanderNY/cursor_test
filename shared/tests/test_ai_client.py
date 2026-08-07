"""Tests for shared ai_client."""

import pytest

from shared.ai_client import (
    CircuitBreaker,
    invalidate_enabled_cache,
    reset_circuit_breaker_for_tests,
)
from shared.circuit_breaker import get_breaker


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(name="ai_test", failure_threshold=2, recovery_timeout_sec=60)
    assert breaker.is_open() is False
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open() is True


def test_circuit_breaker_resets_on_success():
    breaker = CircuitBreaker(name="ai_test", failure_threshold=1, recovery_timeout_sec=60)
    breaker.record_failure()
    assert breaker.is_open() is True
    breaker.record_success()
    assert breaker.is_open() is False


def test_reset_circuit_breaker_for_tests():
    breaker = get_breaker("ai")
    for _ in range(breaker.failure_threshold):
        breaker.record_failure()
    assert breaker.is_open() is True
    reset_circuit_breaker_for_tests()
    assert get_breaker("ai").is_open() is False


@pytest.mark.asyncio
async def test_is_enabled_respects_env_disable(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    invalidate_enabled_cache()
    from shared import ai_client

    assert await ai_client.is_enabled() is False

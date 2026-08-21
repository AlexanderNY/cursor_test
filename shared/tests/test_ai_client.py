"""Tests for shared ai_client."""

import pytest

from shared.ai_client import (
    invalidate_enabled_cache,
    invalidate_availability_cache,
    reset_circuit_breaker_for_tests,
)
from shared.circuit_breaker import CircuitBreaker, get_breaker, reset_breaker_registry_for_tests


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
    reset_breaker_registry_for_tests()
    breaker = get_breaker("ai", failure_threshold=2, recovery_timeout_sec=30)
    for _ in range(breaker.failure_threshold):
        breaker.record_failure()
    assert breaker.is_open() is True
    reset_circuit_breaker_for_tests()
    assert get_breaker("ai").is_open() is False


@pytest.mark.asyncio
async def test_is_enabled_respects_env_disable(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    invalidate_enabled_cache()
    invalidate_availability_cache()
    from shared import ai_client

    assert await ai_client.is_enabled() is False
    assert await ai_client.is_ready() is False


@pytest.mark.asyncio
async def test_probe_unavailable_when_connect_fails(monkeypatch):
    reset_circuit_breaker_for_tests()
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_SERVICE_URL", "http://127.0.0.1:1")
    invalidate_enabled_cache()
    invalidate_availability_cache()

    # Пересоздаём config / client state через reload-подобную инвалидацию.
    from shared import ai_client

    ai_client._config.service_url = "http://127.0.0.1:1"
    ai_client._config.availability_probe_timeout_sec = 0.5
    if ai_client._http_client is not None and not ai_client._http_client.is_closed:
        await ai_client._http_client.aclose()
    ai_client._http_client = None

    assert await ai_client.probe_available(force=True) is False
    assert await ai_client.is_ready() is False


@pytest.mark.asyncio
async def test_summarize_fallback_when_ai_down(monkeypatch):
    reset_circuit_breaker_for_tests()
    monkeypatch.setenv("AI_ENABLED", "true")
    invalidate_enabled_cache()
    invalidate_availability_cache()

    from shared import ai_client

    async def _no(_force: bool = False) -> bool:
        return False

    monkeypatch.setattr(ai_client, "probe_available", _no)
    monkeypatch.setattr(ai_client, "is_enabled", _async_true)

    text = "hello world " * 20
    out = await ai_client.summarize(text, 20)
    assert len(out) <= 23  # truncate + optional ...
    assert out.startswith("hello")


async def _async_true() -> bool:
    return True

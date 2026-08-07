"""Tests for shared.circuit_breaker."""

import time

from shared.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_breaker,
    reset_breaker_registry_for_tests,
)


def test_opens_after_threshold_failures():
    breaker = CircuitBreaker(name="t", failure_threshold=2, recovery_timeout_sec=60)
    assert breaker.allow_request() is True
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False
    assert breaker.is_open() is True


def test_success_resets():
    breaker = CircuitBreaker(name="t", failure_threshold=1, recovery_timeout_sec=60)
    breaker.record_failure()
    assert breaker.is_open() is True
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_half_open_then_close():
    breaker = CircuitBreaker(name="t", failure_threshold=1, recovery_timeout_sec=0.05)
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    time.sleep(0.06)
    assert breaker.allow_request() is True
    assert breaker.state == CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED


def test_half_open_failure_reopens():
    breaker = CircuitBreaker(name="t", failure_threshold=1, recovery_timeout_sec=0.05)
    breaker.record_failure()
    time.sleep(0.06)
    assert breaker.allow_request() is True
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN


def test_registry_singleton():
    reset_breaker_registry_for_tests()
    a = get_breaker("vk_api")
    b = get_breaker("vk_api")
    assert a is b
    reset_breaker_registry_for_tests()

"""Tests for shared ai_client."""

import pytest

from shared.ai_client import CircuitBreaker, reset_circuit_breaker_for_tests


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=60)
    assert breaker.is_open() is False
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open() is True


def test_circuit_breaker_resets_on_success():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_sec=60)
    breaker.record_failure()
    assert breaker.is_open() is True
    breaker.record_success()
    assert breaker.is_open() is False


def test_reset_circuit_breaker_for_tests():
    reset_circuit_breaker_for_tests()

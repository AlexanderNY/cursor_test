"""Tests for shared.retry."""

import pytest

from shared.retry import retry_async, _wait_seconds


def test_wait_exponential_capped():
    assert _wait_seconds(0, 0.5, 8.0) == 0.5
    assert _wait_seconds(1, 0.5, 8.0) == 1.0
    assert _wait_seconds(2, 0.5, 8.0) == 2.0
    assert _wait_seconds(10, 0.5, 8.0) == 8.0


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("down")
        return "ok"

    result = await retry_async(
        flaky,
        attempts=3,
        min_wait_sec=0.0,
        max_wait_sec=0.0,
        retry_on=lambda e: isinstance(e, ConnectionError),
        operation_name="test",
    )
    assert result == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_retry_exhausted_raises():
    calls = {"n": 0}

    async def always_fail() -> None:
        calls["n"] += 1
        raise TimeoutError("timeout")

    with pytest.raises(TimeoutError):
        await retry_async(
            always_fail,
            attempts=3,
            min_wait_sec=0.0,
            max_wait_sec=0.0,
            retry_on=lambda e: isinstance(e, TimeoutError),
            operation_name="test",
        )
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_non_retryable_raises_immediately():
    calls = {"n": 0}

    async def auth_fail() -> None:
        calls["n"] += 1
        raise ValueError("bad token")

    with pytest.raises(ValueError):
        await retry_async(
            auth_fail,
            attempts=5,
            min_wait_sec=0.0,
            max_wait_sec=0.0,
            retry_on=lambda e: isinstance(e, ConnectionError),
            operation_name="test",
        )
    assert calls["n"] == 1

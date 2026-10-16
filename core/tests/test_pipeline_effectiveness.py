"""Unit tests for pipeline effectiveness helpers."""

from services.pipeline_effectiveness import (
    normalize_failure_reason,
    percentile,
    success_rate,
    summarize_latency_minutes,
)


def test_success_rate_ignores_skipped() -> None:
    assert success_rate(8, 2) == 0.8
    assert success_rate(0, 0) is None
    assert success_rate(0, 4) == 0.0


def test_percentile_median_and_p95() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 100.0]
    assert percentile(values, 0.5) == 30.0
    assert percentile([], 0.5) is None
    summary = summarize_latency_minutes(values)
    assert summary["sample_size"] == 5
    assert summary["median_minutes"] == 30.0
    assert summary["p95_minutes"] is not None
    assert summary["p95_minutes"] >= 40.0


def test_latency_drops_negative() -> None:
    summary = summarize_latency_minutes([5.0, -1.0, 15.0])
    assert summary["sample_size"] == 2
    assert summary["median_minutes"] == 10.0


def test_failure_reason_blank_is_unknown() -> None:
    assert normalize_failure_reason("  ") == "unknown"
    assert normalize_failure_reason("timeout") == "timeout"
    long_reason = "x" * 200
    assert len(normalize_failure_reason(long_reason)) == 160

"""Pure helpers for pipeline effectiveness aggregates."""

from __future__ import annotations

from typing import Optional, Sequence


def success_rate(published: int, failed: int) -> Optional[float]:
    """Share of finished attempts that published. Skipped targets are not attempts."""
    done = int(published) + int(failed)
    if done <= 0:
        return None
    return round(int(published) / done, 6)


def percentile(values: Sequence[float], quantile: float) -> Optional[float]:
    """Linear percentile. quantile is 0..1. Empty input returns None."""
    if not values:
        return None
    if quantile <= 0:
        return float(min(values))
    if quantile >= 1:
        return float(max(values))
    ordered = sorted(float(item) for item in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * quantile
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def summarize_latency_minutes(values: Sequence[float]) -> dict[str, Optional[float] | int]:
    """Median and p95 of collect→publish minutes."""
    cleaned = [float(item) for item in values if item is not None and float(item) >= 0]
    median = percentile(cleaned, 0.5)
    p95 = percentile(cleaned, 0.95)
    return {
        "sample_size": len(cleaned),
        "median_minutes": round(median, 2) if median is not None else None,
        "p95_minutes": round(p95, 2) if p95 is not None else None,
    }


def normalize_failure_reason(raw: object, *, limit: int = 160) -> str:
    text = str(raw or "").strip()
    if not text:
        return "unknown"
    if len(text) > limit:
        return text[:limit]
    return text

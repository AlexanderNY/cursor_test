"""In-memory fixed-window rate limit for resume-api (keyed by user_id|bucket)."""
from __future__ import annotations

import os
import threading
import time
from typing import Optional

from fastapi import HTTPException

# bucket -> (limit, window_seconds); overridable via RATE_LIMIT_{BUCKET}_* env
_DEFAULTS: dict[str, tuple[int, int]] = {
    "ai": (8, 60),
    "generate": (20, 60),
    "preview": (60, 60),
    "export": (10, 60),
}

MAX_KEYS = 10_000
_CLEANUP_EVERY = 100

_lock = threading.Lock()
_counts: dict[str, dict[str, float | int]] = {}
_ops = 0


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def bucket_limits(bucket: str) -> tuple[int, int]:
    # Runtime admin overrides (DB cache) win over env.
    try:
        from services.runtime_settings import rate_limit_override

        override = rate_limit_override(bucket)
        if override is not None:
            return override
    except Exception:
        pass

    limit_default, window_default = _DEFAULTS.get(bucket, (30, 60))
    key = bucket.upper()
    limit = _env_int(f"RATE_LIMIT_{key}_REQUESTS", limit_default)
    window = _env_int(f"RATE_LIMIT_{key}_WINDOW_SEC", window_default)
    return limit, window


def _cleanup(now: float) -> None:
    global _counts
    expired = [
        key
        for key, meta in _counts.items()
        if now - float(meta["window_start"]) >= float(meta.get("window_sec", 60))
    ]
    for key in expired:
        _counts.pop(key, None)
    if len(_counts) > MAX_KEYS:
        # Drop oldest windows first
        ordered = sorted(_counts.items(), key=lambda item: float(item[1]["window_start"]))
        for key, _ in ordered[: len(_counts) - MAX_KEYS]:
            _counts.pop(key, None)


def check_rate_limit(
    user_id: int,
    bucket: str,
    *,
    limit: Optional[int] = None,
    window_sec: Optional[int] = None,
) -> dict[str, int]:
    """Increment counter; raise HTTP 429 if over limit. Returns header values."""
    global _ops
    cfg_limit, cfg_window = bucket_limits(bucket)
    max_requests = limit if limit is not None else cfg_limit
    window = window_sec if window_sec is not None else cfg_window
    key = f"{int(user_id)}|{bucket}"
    now = time.monotonic()

    with _lock:
        _ops += 1
        if _ops % _CLEANUP_EVERY == 0 or len(_counts) > MAX_KEYS:
            _cleanup(now)

        meta = _counts.get(key)
        if meta is None or now - float(meta["window_start"]) >= window:
            _counts[key] = {
                "count": 1,
                "window_start": now,
                "window_sec": window,
            }
            remaining = max_requests - 1
            return {
                "limit": max_requests,
                "remaining": max(0, remaining),
                "window": window,
            }

        count = int(meta["count"]) + 1
        meta["count"] = count
        if count > max_requests:
            retry_after = max(
                1,
                int(window - (now - float(meta["window_start"]))) + 1,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for '{bucket}' ({max_requests}/{window}s)",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(window),
                    "Retry-After": str(retry_after),
                },
            )
        remaining = max_requests - count
        return {
            "limit": max_requests,
            "remaining": max(0, remaining),
            "window": window,
        }


def enforce_rate_limit(user_id: int, bucket: str) -> None:
    """Raise 429 when over quota."""
    check_rate_limit(user_id, bucket)


def reset_rate_limits_for_tests() -> None:
    """Clear store (unit tests only)."""
    global _counts, _ops
    with _lock:
        _counts.clear()
        _ops = 0

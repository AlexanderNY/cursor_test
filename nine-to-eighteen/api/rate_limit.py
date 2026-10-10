"""In-memory fixed-window rate limit for site-api (keyed by client IP|bucket)."""
from __future__ import annotations

import threading
import time
from typing import Optional

from fastapi import HTTPException, Request

from config import settings

_DEFAULTS: dict[str, tuple[int, int]] = {
    "auth": (20, 60),
    "contact": (10, 60),
}

MAX_KEYS = 10_000
_CLEANUP_EVERY = 100

_lock = threading.Lock()
_counts: dict[str, dict[str, float | int]] = {}
_ops = 0


def bucket_limits(bucket: str) -> tuple[int, int]:
    if bucket == "auth":
        return (
            max(1, int(settings.RATE_LIMIT_AUTH_REQUESTS)),
            max(1, int(settings.RATE_LIMIT_AUTH_WINDOW_SEC)),
        )
    if bucket == "contact":
        return (
            max(1, int(settings.RATE_LIMIT_CONTACT_REQUESTS)),
            max(1, int(settings.RATE_LIMIT_CONTACT_WINDOW_SEC)),
        )
    return _DEFAULTS.get(bucket, (30, 60))


def client_key(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


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
        ordered = sorted(_counts.items(), key=lambda item: float(item[1]["window_start"]))
        for key, _ in ordered[: len(_counts) - MAX_KEYS]:
            _counts.pop(key, None)


def check_rate_limit(
    key: str,
    bucket: str,
    *,
    limit: Optional[int] = None,
    window_sec: Optional[int] = None,
) -> dict[str, int]:
    """Increment counter; raise HTTP 429 if over limit."""
    global _ops
    cfg_limit, cfg_window = bucket_limits(bucket)
    max_requests = limit if limit is not None else cfg_limit
    window = window_sec if window_sec is not None else cfg_window
    store_key = f"{key}|{bucket}"
    now = time.monotonic()

    with _lock:
        _ops += 1
        if _ops % _CLEANUP_EVERY == 0 or len(_counts) > MAX_KEYS:
            _cleanup(now)

        meta = _counts.get(store_key)
        if meta is None or now - float(meta["window_start"]) >= window:
            _counts[store_key] = {
                "count": 1,
                "window_start": now,
                "window_sec": window,
            }
            return {
                "limit": max_requests,
                "remaining": max(0, max_requests - 1),
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
        return {
            "limit": max_requests,
            "remaining": max(0, max_requests - count),
            "window": window,
        }


def enforce_rate_limit(request: Request, bucket: str) -> None:
    check_rate_limit(client_key(request), bucket)


def reset_rate_limits_for_tests() -> None:
    global _counts, _ops
    with _lock:
        _counts.clear()
        _ops = 0

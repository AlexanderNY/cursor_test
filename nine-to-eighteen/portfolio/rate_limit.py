"""In-memory fixed-window rate limit for portfolio-api.

Single-process only — quotas do not share across replicas.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from fastapi import HTTPException, Request

from config import settings

MAX_KEYS = 10_000
_CLEANUP_EVERY = 100

_lock = threading.Lock()
_counts: dict[str, dict[str, float | int]] = {}
_ops = 0


def bucket_limits(bucket: str) -> tuple[int, int]:
    if bucket == "write":
        return (
            max(1, int(settings.RATE_LIMIT_WRITE_REQUESTS)),
            max(1, int(settings.RATE_LIMIT_WRITE_WINDOW_SEC)),
        )
    if bucket == "public":
        return (
            max(1, int(settings.RATE_LIMIT_PUBLIC_REQUESTS)),
            max(1, int(settings.RATE_LIMIT_PUBLIC_WINDOW_SEC)),
        )
    return (30, 60)


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
        for key, _meta in ordered[: len(_counts) - MAX_KEYS]:
            _counts.pop(key, None)


def check_rate_limit(
    key: str,
    bucket: str,
    *,
    limit: Optional[int] = None,
    window_sec: Optional[int] = None,
) -> None:
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
            return

        count = int(meta["count"]) + 1
        meta["count"] = count
        if count > max_requests:
            retry_after = max(1, int(window - (now - float(meta["window_start"]))) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for '{bucket}' ({max_requests}/{window}s)",
                headers={"Retry-After": str(retry_after)},
            )


def enforce_write_limit(user_id: int) -> None:
    check_rate_limit(str(int(user_id)), "write")


def enforce_public_limit(request: Request) -> None:
    check_rate_limit(client_key(request), "public")

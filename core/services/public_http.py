"""Fetch a public http(s) document with one validated redirect and a size cap."""

from __future__ import annotations

from shared.safe_fetch import MAX_TEXT_BYTES, FetchTooLargeError, fetch_bounded
from shared.url_safety import UnsafeUrlError


async def fetch_public_http_text(
    url: str,
    *,
    timeout: float = 20.0,
    max_bytes: int = MAX_TEXT_BYTES,
) -> str:
    """GET url after SSRF checks. Follow at most one redirect, re-checked."""
    try:
        body, _content_type = await fetch_bounded(
            url,
            timeout=timeout,
            max_bytes=max_bytes,
        )
    except FetchTooLargeError as exc:
        raise UnsafeUrlError("Response is too large") from exc
    return body.decode("utf-8", errors="replace")

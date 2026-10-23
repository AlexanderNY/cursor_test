"""Fetch a public http(s) document with one validated redirect."""

from __future__ import annotations

from urllib.parse import urljoin

import httpx

from shared.url_safety import UnsafeUrlError, validate_public_http_url

_REDIRECTS = frozenset({301, 302, 303, 307, 308})


async def fetch_public_http_text(url: str, *, timeout: float = 20.0) -> str:
    """GET url after SSRF checks. Follow at most one redirect, re-checked."""
    safe = validate_public_http_url(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.get(safe)
        if response.status_code in _REDIRECTS:
            location = (response.headers.get("location") or "").strip()
            if not location:
                raise UnsafeUrlError("Redirect without Location")
            next_url = validate_public_http_url(urljoin(str(response.url), location))
            response = await client.get(next_url)
            if response.status_code in _REDIRECTS:
                raise UnsafeUrlError("Too many redirects")
        response.raise_for_status()
        return response.text

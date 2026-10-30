"""Bounded HTTP fetch: public URLs only, one re-checked redirect, size cap.

Trusted bases are exact origins (scheme, host, port) of our own services.
Use them only when this process rewrote a relative storage path into that origin.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from urllib.parse import urljoin, urlparse

import httpx

from shared.url_safety import UnsafeUrlError, validate_public_http_url

MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 1

_REDIRECTS = frozenset({301, 302, 303, 307, 308})


class FetchError(Exception):
    """Outbound fetch failed or was rejected."""


class FetchTooLargeError(FetchError):
    """Response body exceeds the configured byte cap."""


def _origin(url: str) -> str:
    parsed = urlparse((url or "").strip())
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower().rstrip(".")
    if scheme not in {"http", "https"} or not host:
        return ""
    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80
    return f"{scheme}://{host}:{port}"


def _is_trusted_origin(url: str, trusted_bases: Sequence[str]) -> bool:
    origin = _origin(url)
    if not origin:
        return False
    for base in trusted_bases:
        if base and _origin(base) == origin:
            return True
    return False


def _authorize_url(url: str, trusted_bases: Sequence[str]) -> str:
    if _is_trusted_origin(url, trusted_bases):
        parsed = urlparse(url.strip())
        if parsed.username is not None or parsed.password is not None:
            raise UnsafeUrlError("URLs with credentials are not allowed")
        return url.strip()
    return validate_public_http_url(url)


async def fetch_bounded(
    url: str,
    *,
    max_bytes: int = MAX_DOWNLOAD_BYTES,
    timeout: float = 30.0,
    trusted_bases: Sequence[str] = (),
    max_redirects: int = MAX_REDIRECTS,
    headers: Mapping[str, str] | None = None,
) -> tuple[bytes, str]:
    """GET url and return (body, content-type).

    Public URLs pass validate_public_http_url. Redirect targets are checked again.
    """
    current = (url or "").strip()
    if not current:
        raise UnsafeUrlError("URL is empty")
    if max_bytes <= 0:
        raise FetchError("Download limit misconfigured")

    request_headers = {"User-Agent": "CopyParse/1.0"}
    if headers:
        request_headers.update(dict(headers))

    redirects_left = max(0, int(max_redirects))
    target = _authorize_url(current, trusted_bases)
    try:
        return await _read_checked(
            target,
            trusted_bases=trusted_bases,
            max_bytes=max_bytes,
            timeout=timeout,
            redirects_left=redirects_left,
            request_headers=request_headers,
        )
    except httpx.HTTPError as exc:
        raise FetchError(str(exc)) from exc


async def _read_checked(
    target: str,
    *,
    trusted_bases: Sequence[str],
    max_bytes: int,
    timeout: float,
    redirects_left: int,
    request_headers: dict[str, str],
) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        while True:
            async with client.stream("GET", target, headers=request_headers) as response:
                if response.status_code in _REDIRECTS:
                    location = (response.headers.get("location") or "").strip()
                    if not location:
                        raise UnsafeUrlError("Redirect without Location")
                    if redirects_left <= 0:
                        raise UnsafeUrlError("Too many redirects")
                    redirects_left -= 1
                    current = urljoin(str(response.url), location)
                    target = _authorize_url(current, trusted_bases)
                    continue
                if response.status_code >= 400:
                    raise FetchError(f"HTTP {response.status_code}")
                declared = response.headers.get("content-length")
                if declared:
                    try:
                        if int(declared) > max_bytes:
                            raise FetchTooLargeError("Response is too large")
                    except ValueError as exc:
                        raise FetchError("Invalid Content-Length") from exc
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes(65536):
                    total += len(chunk)
                    if total > max_bytes:
                        raise FetchTooLargeError("Response is too large")
                    chunks.append(chunk)
                content_type = response.headers.get("content-type") or ""
                return b"".join(chunks), content_type

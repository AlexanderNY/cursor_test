"""Защита от SSRF: валидация URL перед серверным запросом."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

_ALLOWED_SCHEMES = frozenset({"http", "https"})

_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata",
        "metadata.google.internal",
        "metadata.goog",
        "instance-data",
        "kubernetes.default",
        "kubernetes.default.svc",
    }
)


class UnsafeUrlError(ValueError):
    """URL небезопасен для серверного fetch (SSRF)."""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True для loopback / private / link-local / reserved / multicast и т.п."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _resolve_host_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Резолвит hostname во все A/AAAA; при ошибке DNS — UnsafeUrlError."""
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"DNS resolution failed for host: {hostname}") from exc

    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    seen: set[str] = set()
    for info in infos:
        addr = info[4][0]
        if addr in seen:
            continue
        seen.add(addr)
        try:
            ips.append(ipaddress.ip_address(addr))
        except ValueError:
            continue
    if not ips:
        raise UnsafeUrlError(f"No IP addresses resolved for host: {hostname}")
    return ips


def _normalized_http_url(raw: str) -> tuple[str, str, ipaddress.IPv4Address | ipaddress.IPv6Address | None]:
    """Shape checks shared by save-time and fetch-time validation. No DNS."""
    text = (raw or "").strip()
    if not text:
        raise UnsafeUrlError("URL is empty")

    parsed = urlparse(text)
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError("Only http and https URLs are allowed")

    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("URLs with credentials are not allowed")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise UnsafeUrlError("URL host is required")

    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise UnsafeUrlError("Host is not allowed")

    port = parsed.port
    if port is not None and port not in (80, 443):
        raise UnsafeUrlError("Only ports 80 and 443 are allowed")

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None and _is_blocked_ip(literal_ip):
        raise UnsafeUrlError("IP address is not allowed (private or reserved)")

    if isinstance(literal_ip, ipaddress.IPv6Address):
        host_part = f"[{hostname}]"
    else:
        host_part = hostname

    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{host_part}:{port}"
    else:
        netloc = host_part

    normalized = urlunparse((scheme, netloc, parsed.path or "", "", parsed.query, ""))
    return normalized, hostname, literal_ip


def validate_http_url_shape(url: str) -> str:
    """Проверяет схему, порт и литеральные адреса без DNS.

    Используется при сохранении профиля: внутренняя сеть отсекается повторно
    в момент запроса, когда резолв уже известен.
    """
    normalized, _hostname, _literal = _normalized_http_url(url)
    return normalized


def validate_public_http_url(url: str) -> str:
    """
    Проверяет URL на SSRF-риски и возвращает нормализованную строку (без credentials/fragment).

    - только http/https
    - без userinfo
    - порт только 80/443 (или default схемы)
    - hostname не из blocklist
    - все резолвленные IP — публичные
    """
    normalized, hostname, literal_ip = _normalized_http_url(url)
    if literal_ip is None:
        for ip in _resolve_host_ips(hostname):
            if _is_blocked_ip(ip):
                raise UnsafeUrlError("Host resolves to a private or reserved IP")
    return normalized

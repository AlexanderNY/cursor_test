"""Unit tests for SSRF URL validation (no Selenium)."""

from __future__ import annotations

import ipaddress
from unittest.mock import patch

import pytest

from services.url_safety import UnsafeUrlError, validate_public_http_url


def test_rejects_non_http_schemes() -> None:
    for url in ("file:///etc/passwd", "ftp://example.com/", "data:text/html,hi", "javascript:alert(1)"):
        with pytest.raises(UnsafeUrlError):
            validate_public_http_url(url)


def test_rejects_credentials() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url("https://user:pass@example.com/")


def test_rejects_localhost_and_loopback() -> None:
    for url in (
        "http://localhost/",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://0.0.0.0/",
    ):
        with pytest.raises(UnsafeUrlError):
            validate_public_http_url(url)


def test_rejects_private_literals() -> None:
    for url in (
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",
    ):
        with pytest.raises(UnsafeUrlError):
            validate_public_http_url(url)


def test_rejects_nonstandard_ports() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url("https://example.com:8443/")
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url("http://example.com:8080/")


def test_rejects_host_resolving_to_private() -> None:
    fake = [
        (None, None, None, None, ("10.1.2.3", 0)),
    ]
    with patch("services.url_safety.socket.getaddrinfo", return_value=fake):
        with pytest.raises(UnsafeUrlError, match="private"):
            validate_public_http_url("https://evil.example/")


def test_allows_public_literal_and_host() -> None:
    # 8.8.8.8 is global unicast (Google DNS) — not private
    assert validate_public_http_url("https://8.8.8.8/path") == "https://8.8.8.8/path"

    fake = [
        (None, None, None, None, ("93.184.216.34", 0)),
    ]
    with patch("services.url_safety.socket.getaddrinfo", return_value=fake):
        out = validate_public_http_url("https://Example.COM/foo?q=1#frag")
        assert out == "https://example.com/foo?q=1"
        assert "#frag" not in out


def test_blocked_ip_helper_maps_ipv4_mapped() -> None:
    from services.url_safety import _is_blocked_ip

    assert _is_blocked_ip(ipaddress.ip_address("::ffff:127.0.0.1")) is True
    assert _is_blocked_ip(ipaddress.ip_address("8.8.8.8")) is False

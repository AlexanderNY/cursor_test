"""Bounded fetch rejects unsafe URLs before opening a client."""

from unittest.mock import patch

import pytest

from shared.safe_fetch import fetch_bounded
from shared.url_safety import UnsafeUrlError, validate_http_url_shape
from shared.xml_safety import assert_safe_xml


def test_shape_rejects_file_and_loopback_without_dns() -> None:
    for url in ("file:///etc/passwd", "http://127.0.0.1/", "http://169.254.169.254/"):
        with pytest.raises(UnsafeUrlError):
            validate_http_url_shape(url)


def test_shape_allows_public_host_without_dns() -> None:
    assert validate_http_url_shape("https://Example.COM/rss") == "https://example.com/rss"


@pytest.mark.asyncio
async def test_fetch_loopback_does_not_open_client() -> None:
    with patch("shared.safe_fetch.httpx.AsyncClient") as client_cls:
        with pytest.raises(UnsafeUrlError):
            await fetch_bounded("http://127.0.0.1/latest/meta-data/")
        client_cls.assert_not_called()


def test_xml_rejects_doctype() -> None:
    with pytest.raises(ValueError):
        assert_safe_xml("<!DOCTYPE foo [<!ENTITY x 'y'>]><rss></rss>")

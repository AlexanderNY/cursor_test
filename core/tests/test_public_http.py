"""RSS fetch must reject private URLs before opening a client."""

from unittest.mock import patch

import pytest

from services.public_http import fetch_public_http_text
from shared.url_safety import UnsafeUrlError


@pytest.mark.asyncio
async def test_loopback_rss_url_does_not_open_http_client() -> None:
    with patch("services.public_http.httpx.AsyncClient") as client_cls:
        with pytest.raises(UnsafeUrlError):
            await fetch_public_http_text("http://127.0.0.1/latest/meta-data/")
        client_cls.assert_not_called()

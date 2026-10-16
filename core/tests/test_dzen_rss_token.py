"""Dzen RSS requires a non-empty matching token."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from routers import dzen as dzen_router


@pytest.mark.asyncio
async def test_rss_rejects_missing_token():
    with patch.object(
        dzen_router.profile_service,
        "get_dzen_profile",
        new=AsyncMock(return_value={"rss_token": "secret", "channel_name": "x"}),
    ):
        with pytest.raises(HTTPException) as exc:
            await dzen_router.get_dzen_rss(user_id=1, token=None)
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_rss_rejects_empty_profile_token():
    with patch.object(
        dzen_router.profile_service,
        "get_dzen_profile",
        new=AsyncMock(return_value={"rss_token": None, "channel_name": "x"}),
    ):
        with pytest.raises(HTTPException) as exc:
            await dzen_router.get_dzen_rss(user_id=1, token="anything")
        assert exc.value.status_code == 403

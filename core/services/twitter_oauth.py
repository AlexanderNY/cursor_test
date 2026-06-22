"""OAuth 2.0 refresh и вспомогательные вызовы X API v2 (Core)."""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import httpx

from config import settings

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.twitter.com/2/oauth2/token"


def access_token_expired(expires_at: Optional[datetime], buffer_sec: int = 120) -> bool:
    if expires_at is None:
        return True
    return datetime.utcnow() + timedelta(seconds=buffer_sec) >= expires_at


async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    cid = (settings.TWITTER_CLIENT_ID or "").strip()
    csec = (settings.TWITTER_CLIENT_SECRET or "").strip()
    if not cid or not csec or not refresh_token:
        return None
    basic = base64.b64encode(f"{cid}:{csec}".encode("utf-8")).decode("ascii")
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": cid,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                TOKEN_URL,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=body,
            )
            data = resp.json()
            if resp.status_code >= 400:
                logger.warning("Twitter token refresh failed: %s", data)
                return None
            return data
    except Exception as e:
        logger.exception("Twitter token refresh error: %s", e)
        return None


async def ensure_user_access_token(
    access_token: Optional[str],
    refresh_token: Optional[str],
    expires_at: Optional[datetime],
) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
    if access_token and not access_token_expired(expires_at):
        return access_token, refresh_token, expires_at
    if not refresh_token:
        return None, refresh_token, expires_at
    data = await refresh_access_token(refresh_token)
    if not data or not data.get("access_token"):
        return None, refresh_token, expires_at
    new_access = data["access_token"]
    new_refresh = data.get("refresh_token") or refresh_token
    new_expires = None
    if data.get("expires_in") is not None:
        try:
            new_expires = datetime.utcnow() + timedelta(seconds=int(data["expires_in"]))
        except (TypeError, ValueError):
            pass
    return new_access, new_refresh, new_expires

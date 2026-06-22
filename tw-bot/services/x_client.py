"""HTTP-клиент X API v2: токены и запросы."""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TWEETS_CREATE = "https://api.twitter.com/2/tweets"


async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Обновляет access_token по refresh_token (OAuth 2.0)."""
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
                logger.warning("Token refresh failed: %s", data)
                return None
            return data
    except Exception as e:
        logger.exception("Token refresh error: %s", e)
        return None


def access_token_expired(expires_at: Optional[datetime], buffer_sec: int = 120) -> bool:
    if expires_at is None:
        return True
    return datetime.utcnow() + timedelta(seconds=buffer_sec) >= expires_at


async def ensure_user_access_token(
    access_token: Optional[str],
    refresh_token: Optional[str],
    expires_at: Optional[datetime],
) -> tuple[Optional[str], Optional[str], Optional[datetime]]:
    """Возвращает актуальный access_token и при необходимости обновлённые refresh/expires."""
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


async def create_tweet(access_token: str, text: str) -> Optional[Dict[str, Any]]:
    """POST /2/tweets."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                TWEETS_CREATE,
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"text": text},
            )
            data = resp.json()
            if resp.status_code >= 400:
                logger.warning("create_tweet failed %s: %s", resp.status_code, data)
                return None
            return data
    except Exception as e:
        logger.exception("create_tweet: %s", e)
        return None


async def fetch_timeline_tweets(
    access_token: str,
    user_rest_id: str,
) -> List[Dict[str, Any]]:
    """Пробует reverse chronological home timeline, затем user tweets."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"max_results": 10, "tweet.fields": "created_at,public_metrics"}
    urls = [
        f"https://api.twitter.com/2/users/{user_rest_id}/timelines/reverse_chronological",
        f"https://api.twitter.com/2/users/{user_rest_id}/tweets",
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            try:
                resp = await client.get(url, headers=headers, params=params)
                data = resp.json()
                if resp.status_code == 200:
                    rows = data.get("data") or []
                    if isinstance(rows, list):
                        return rows
                logger.debug("Timeline %s -> %s %s", url, resp.status_code, data)
            except Exception as e:
                logger.warning("Timeline fetch %s: %s", url, e)
    return []

"""Роутер для Twitter / X профилей и постов."""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse

from config import settings
from schemas import TwitterProfileCreate, TwitterPost, TwitterFollowingResponse, TwitterFollowingUser
from services.post_service import post_service
from services.profile_service import profile_service
from services.twitter_oauth import ensure_user_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tw", tags=["Twitter"])

TWITTER_SCOPES = "tweet.read tweet.write users.read follows.read offline.access"
TWITTER_AUTH_URL = "https://x.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TWITTER_API_ME = "https://api.twitter.com/2/users/me"


def _following_url(user_rest_id: str) -> str:
    return f"https://api.twitter.com/2/users/{user_rest_id}/following"


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


@router.get("/profile")
async def get_tw_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль Twitter пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_tw_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "use_proxy": False,
        "proxy_user": None,
        "proxy_pass": None,
        "proxy_host": None,
        "proxy_port": None,
        "twitter_username": None,
        "twitter_password": None,
        "take_screenshot_collect": False,
        "screenshot_xpath": None,
        "twitter_connected": False,
        "twitter_rest_id": None,
    }


@router.post("/profile")
async def save_tw_profile(
    data: TwitterProfileCreate,
    x_user_id: Optional[str] = Header(None),
):
    """Сохраняет профиль Twitter пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_tw_profile(user_id, data.model_dump())
    return profile


@router.get("/profiles")
async def get_all_tw_profiles():
    """Получает все профили Twitter (админка)."""
    profiles = await profile_service.get_all_tw_profiles()
    return {"profiles": profiles}


@router.get("/posts")
async def get_tw_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Список постов tw_posts пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    return await post_service.get_tw_posts(user_id=user_id, limit=limit, offset=offset)


@router.post("/post")
async def create_tw_post(
    data: TwitterPost,
    x_user_id: Optional[str] = Header(None),
):
    """Создаёт запись в tw_posts (max 280 символов)."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        post = await post_service.create_tw_post_record(
            user_id=user_id,
            text=data.text,
            to_tg=data.to_tg,
            to_tw=data.to_tw,
            to_wp=data.to_wp,
            to_vk=data.to_vk,
            to_threads=data.to_threads,
            to_dzen=data.to_dzen,
            to_instagram=data.to_instagram,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/url")
async def get_tw_oauth_url(x_user_id: Optional[str] = Header(None)):
    """URL OAuth 2.0 PKCE для X (Twitter)."""
    user_id = get_user_id_from_header(x_user_id)
    client_id = (getattr(settings, "TWITTER_CLIENT_ID", None) or "").strip()
    redirect_uri = (getattr(settings, "TWITTER_OAUTH_REDIRECT_URI", None) or "").strip()
    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=503,
            detail="X OAuth is not configured (TWITTER_CLIENT_ID, TWITTER_OAUTH_REDIRECT_URI)",
        )
    code_verifier = secrets.token_urlsafe(32)
    challenge = _pkce_challenge(code_verifier)
    expires = datetime.utcnow() + timedelta(minutes=10)
    await profile_service.set_tw_oauth_pkce(user_id, code_verifier, expires)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": TWITTER_SCOPES,
        "state": str(user_id),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{TWITTER_AUTH_URL}?{urlencode(params)}"
    return {"url": url}


@router.get("/oauth/status")
async def tw_oauth_status(x_user_id: Optional[str] = Header(None)):
    """Статус OAuth X."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_tw_profile(user_id)
    if not profile:
        return {"twitter_connected": False, "twitter_rest_id": None}
    return {
        "twitter_connected": bool(profile.get("twitter_connected")),
        "twitter_rest_id": profile.get("twitter_rest_id"),
    }


@router.get("/following", response_model=TwitterFollowingResponse)
async def tw_following(
    x_user_id: Optional[str] = Header(None),
    max_results: int = 50,
    pagination_token: Optional[str] = None,
):
    """Список подписок (following) через X API v2; требует OAuth с scope follows.read."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_tw_oauth_tokens_raw(user_id)
    if not raw:
        raise HTTPException(status_code=400, detail="No Twitter profile")
    rest_id = (raw.get("twitter_rest_id") or "").strip()
    if not rest_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X user id; connect OAuth first",
        )

    mr = max(1, min(max_results, 1000))
    acc = raw.get("twitter_oauth_access_token")
    ref = raw.get("twitter_oauth_refresh_token")
    exp = raw.get("twitter_oauth_expires_at")

    new_acc, new_ref, new_exp = await ensure_user_access_token(acc, ref, exp)
    if not new_acc:
        raise HTTPException(
            status_code=401,
            detail="No valid OAuth access token; reconnect X",
        )
    if new_acc != acc or (new_ref and new_ref != ref) or new_exp != exp:
        await profile_service.persist_tw_oauth_tokens_refreshed(
            user_id, new_acc, new_ref, new_exp
        )

    params: dict[str, Any] = {
        "max_results": mr,
        "user.fields": "username,name",
    }
    if pagination_token:
        params["pagination_token"] = pagination_token

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                _following_url(rest_id),
                headers={"Authorization": f"Bearer {new_acc}"},
                params=params,
            )
            data = resp.json()
    except Exception as e:
        logger.exception("Twitter following request: %s", e)
        raise HTTPException(status_code=502, detail="X API request failed") from e

    if resp.status_code >= 400:
        err_parts: list[str] = []
        errs = data.get("errors")
        if isinstance(errs, list) and errs:
            e0 = errs[0] if isinstance(errs[0], dict) else {}
            err_parts.append(
                str(
                    e0.get("detail")
                    or e0.get("message")
                    or e0.get("title")
                    or errs[0]
                )
            )
        err = (
            err_parts[0]
            if err_parts
            else (data.get("detail") or data.get("title") or str(data))
        )
        if resp.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=f"X API denied (reconnect OAuth with follows.read): {err}",
            )
        raise HTTPException(status_code=resp.status_code, detail=str(err)[:2000])

    rows = data.get("data") or []
    users_out: list[TwitterFollowingUser] = []
    if isinstance(rows, list):
        for u in rows:
            if not isinstance(u, dict):
                continue
            uid = u.get("id")
            if not uid:
                continue
            users_out.append(
                TwitterFollowingUser(
                    id=str(uid),
                    username=u.get("username"),
                    name=u.get("name"),
                )
            )
    meta = data.get("meta") or {}
    next_tok = meta.get("next_token") if isinstance(meta, dict) else None
    return TwitterFollowingResponse(users=users_out, next_token=next_tok)


@router.get("/oauth/callback")
async def tw_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Callback OAuth 2.0: обмен code на токены."""
    frontend_url = (settings.FRONTEND_URL or "").rstrip("/")
    tw_page = f"{frontend_url}/twitter"

    def _redirect_err(msg: str) -> RedirectResponse:
        return RedirectResponse(url=f"{tw_page}?oauth=error&message={quote(msg)}")

    if error:
        msg = error_description or error
        return _redirect_err(msg)
    if not code or not state:
        return _redirect_err("missing_code_or_state")
    try:
        user_id = int(state)
    except (ValueError, TypeError):
        return _redirect_err("invalid_state")

    client_id = (getattr(settings, "TWITTER_CLIENT_ID", None) or "").strip()
    client_secret = (getattr(settings, "TWITTER_CLIENT_SECRET", None) or "").strip()
    redirect_uri = (getattr(settings, "TWITTER_OAUTH_REDIRECT_URI", None) or "").strip()
    if not client_id or not client_secret or not redirect_uri:
        return _redirect_err("server_config")

    code_verifier = await profile_service.get_tw_oauth_pkce(user_id)
    if not code_verifier:
        return _redirect_err("pkce_expired")

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "client_id": client_id,
    }
    data: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                TWITTER_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=body,
            )
            data = resp.json()
            if resp.status_code >= 400:
                err = data.get("error_description") or data.get("error") or resp.text
                logger.warning("Twitter token exchange failed: %s", err)
                await profile_service.clear_tw_oauth_pkce(user_id)
                return _redirect_err("exchange_failed")
    except Exception as e:
        logger.exception("Twitter token exchange: %s", e)
        await profile_service.clear_tw_oauth_pkce(user_id)
        return _redirect_err("exchange_failed")

    access_token = data.get("access_token")
    if not access_token:
        await profile_service.clear_tw_oauth_pkce(user_id)
        return _redirect_err("no_token")

    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in")
    expires_at = None
    if expires_in is not None:
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        except (TypeError, ValueError):
            pass

    twitter_rest_id: Optional[str] = None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            me = await client.get(
                TWITTER_API_ME,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"user.fields": "id,name,username"},
            )
            if me.status_code == 200:
                me_json = me.json()
                twitter_rest_id = (me_json.get("data") or {}).get("id")
    except Exception as e:
        logger.warning("Twitter users/me: %s", e)

    await profile_service.save_tw_oauth_tokens(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        twitter_rest_id=twitter_rest_id,
    )
    return RedirectResponse(url=f"{tw_page}?oauth=success")


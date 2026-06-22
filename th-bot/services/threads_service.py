"""Сервис для OAuth URL и статуса Threads (профили в БД)."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import settings
from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

META_OAUTH_BASE = "https://www.facebook.com/v18.0/dialog/oauth"
THREADS_GRAPH_ME = "https://graph.facebook.com/v18.0/me"
THREADS_GRAPH_PERMISSIONS = "https://graph.facebook.com/v18.0/me/permissions"
DEBUG_TOKEN_URL = "https://graph.facebook.com/debug_token"


def _scopes_from_debug_payload(data: dict) -> list:
    """Извлекает список scope из ответа debug_token."""
    out: list = []
    raw = data.get("scopes")
    if isinstance(raw, list):
        out = [str(s) for s in raw]
    elif isinstance(raw, str) and raw.strip():
        out = [raw.strip()]
    return out


async def fetch_me_permissions(access_token: str) -> tuple[list, Optional[str]]:
    """
    GET /me/permissions — разрешения, выданные приложению (аналог «подписок» на методы API).
    Возвращает (data[], error_message | None).
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(
                THREADS_GRAPH_PERMISSIONS,
                params={"access_token": access_token},
            )
            body = r.json()
            if r.status_code == 200 and isinstance(body.get("data"), list):
                return body["data"], None
            err = (body.get("error") or {}).get("message") or body.get("error_description")
            if not err:
                err = r.text[:300] if r.text else f"HTTP {r.status_code}"
            return [], err
        except httpx.HTTPError as e:
            return [], str(e)


def _token_expired_locally(expires_at: Any) -> bool:
    """True если token_expires_at в прошлом (локальные часы)."""
    if expires_at is None:
        return False
    if isinstance(expires_at, str):
        try:
            raw = expires_at.replace("Z", "+00:00")
            expires_at = datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return False
    if not isinstance(expires_at, datetime):
        return False
    now = datetime.now(timezone.utc)
    exp = expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp < now


async def get_threads_profile(user_id: int) -> Optional[dict]:
    """Читает профиль Threads из БД (включая access_token для бота)."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, access_token, token_expires_at, threads_user_id,
                       publish_enabled, schedule_type, time_intervals
                FROM threads_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            desc = [c.name for c in cur.description]
            return dict(zip(desc, row))
    finally:
        release_db_connection(conn)


async def get_auth_status(user_id: int) -> dict:
    """Возвращает статус OAuth: connected, expires_at, connected_effective (без токена)."""
    profile = await get_threads_profile(user_id)
    if not profile:
        return {
            "user_id": user_id,
            "connected": False,
            "connected_effective": False,
            "expires_at": None,
            "token_expired_locally": False,
            "threads_user_id": None,
            "message": "Profile not found",
        }
    has_token = bool(profile.get("access_token"))
    expires_at = profile.get("token_expires_at")
    expired_loc = _token_expired_locally(expires_at) if has_token else False
    connected_effective = has_token and not expired_loc
    msg = "Not connected"
    if has_token:
        msg = "Token expired (by local expiry time)" if expired_loc else "Connected"
    return {
        "user_id": user_id,
        "connected": has_token,
        "connected_effective": connected_effective,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "token_expired_locally": expired_loc,
        "threads_user_id": profile.get("threads_user_id"),
        "message": msg,
    }


async def _persist_threads_user_id_if_empty(user_id: int, threads_user_id: str) -> None:
    """Подставляет threads_user_id из Graph, если в БД пусто."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE threads_profiles
                SET threads_user_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND (threads_user_id IS NULL OR threads_user_id = '')
                """,
                (threads_user_id, user_id),
            )
    finally:
        release_db_connection(conn)


async def verify_threads_auth(user_id: int) -> dict:
    """
    Проверяет токен у Meta: debug_token (если заданы META_APP_ID/SECRET), иначе GET /me.
    """
    profile = await get_threads_profile(user_id)
    if not profile:
        return {
            "user_id": user_id,
            "valid": False,
            "message": "Profile not found",
            "threads_user_id": None,
            "graph_user_id": None,
            "expires_at": None,
            "token_expired_locally": False,
            "persisted_threads_user_id": False,
            "scopes": [],
            "permissions": [],
            "permissions_error": None,
        }
    token = (profile.get("access_token") or "").strip()
    if not token:
        return {
            "user_id": user_id,
            "valid": False,
            "message": "No access token",
            "threads_user_id": profile.get("threads_user_id"),
            "graph_user_id": None,
            "expires_at": profile.get("token_expires_at").isoformat()
            if profile.get("token_expires_at")
            else None,
            "token_expired_locally": False,
            "persisted_threads_user_id": False,
            "scopes": [],
            "permissions": [],
            "permissions_error": None,
        }

    expires_at = profile.get("token_expires_at")
    expired_loc = _token_expired_locally(expires_at)
    threads_user_id_db = profile.get("threads_user_id")
    app_id = (settings.META_APP_ID or "").strip()
    app_secret = (settings.META_APP_SECRET or "").strip()

    meta_valid: Optional[bool] = None
    graph_user_id: Optional[str] = None
    err_msg: Optional[str] = None
    scopes_from_debug: list = []

    async with httpx.AsyncClient(timeout=25.0) as client:
        if app_id and app_secret:
            try:
                r = await client.get(
                    DEBUG_TOKEN_URL,
                    params={
                        "input_token": token,
                        "access_token": f"{app_id}|{app_secret}",
                    },
                )
                body = r.json()
                if r.status_code == 200 and "data" in body:
                    data = body.get("data") or {}
                    meta_valid = bool(data.get("is_valid"))
                    scopes_from_debug = _scopes_from_debug_payload(data)
                    uid = data.get("user_id")
                    if uid is not None:
                        graph_user_id = str(uid)
                    if not meta_valid:
                        err_msg = (body.get("error") or {}).get("message") or "Token not valid"
                else:
                    err_msg = (body.get("error") or {}).get("message") or r.text[:300]
            except (httpx.HTTPError, ValueError, TypeError) as e:
                logger.warning("debug_token failed, falling back to /me: %s", e)
                meta_valid = None

        if meta_valid is None:
            try:
                r = await client.get(
                    THREADS_GRAPH_ME,
                    params={"access_token": token, "fields": "id,name"},
                )
                if r.status_code == 200:
                    j = r.json()
                    meta_valid = True
                    gid = j.get("id")
                    if gid is not None:
                        graph_user_id = str(gid)
                else:
                    meta_valid = False
                    try:
                        err_msg = (r.json().get("error") or {}).get("message") or r.text[:300]
                    except (ValueError, TypeError, AttributeError):
                        err_msg = r.text[:300]
            except httpx.HTTPError as e:
                meta_valid = False
                err_msg = str(e)

    persisted = False
    if meta_valid and graph_user_id and not threads_user_id_db:
        await _persist_threads_user_id_if_empty(user_id, graph_user_id)
        persisted = True
        threads_user_id_db = graph_user_id

    valid = bool(meta_valid is True) and not expired_loc

    if meta_valid is True and not expired_loc:
        message = "Token is valid with Meta"
    elif meta_valid is True and expired_loc:
        message = "Meta accepted token but local expiry time has passed; reconnect if publishing fails"
    elif meta_valid is False:
        message = err_msg or "Token invalid or revoked"
    else:
        message = err_msg or "Could not verify token"

    permissions_list, permissions_err = await fetch_me_permissions(token)

    return {
        "user_id": user_id,
        "valid": valid,
        "message": message,
        "threads_user_id": threads_user_id_db,
        "graph_user_id": graph_user_id,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "token_expired_locally": expired_loc,
        "persisted_threads_user_id": persisted,
        "scopes": scopes_from_debug,
        "permissions": permissions_list,
        "permissions_error": permissions_err,
    }


def build_oauth_url(user_id: int) -> str:
    """Собирает URL для редиректа пользователя на Meta OAuth (state = user_id)."""
    app_id = (settings.META_APP_ID or "").strip()
    redirect_uri = (settings.THREADS_OAUTH_REDIRECT_URI or "").strip()
    scope = (settings.THREADS_OAUTH_SCOPE or "threads_basic,threads_content_publish").strip()
    if not app_id or not redirect_uri:
        return ""
    from urllib.parse import urlencode
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": str(user_id),
        "response_type": "code",
    }
    return f"{META_OAUTH_BASE}?{urlencode(params)}"


async def get_pending_posts_for_user(user_id: int, limit: int = 10) -> list:
    """Посты пользователя со статусом collected/ready к публикации в Threads."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, post_text, images, status
                FROM threads_posts
                WHERE user_id = %s AND status NOT IN ('deleted', 'published')
                ORDER BY created_at ASC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = await cur.fetchall()
            desc = [c.name for c in cur.description]
            return [dict(zip(desc, row)) for row in rows]
    finally:
        release_db_connection(conn)


async def set_post_status(user_id: int, post_id: int, status: str) -> None:
    """Обновляет статус поста (например published или failed)."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE threads_posts SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s AND id = %s",
                (status, user_id, post_id),
            )
    finally:
        release_db_connection(conn)

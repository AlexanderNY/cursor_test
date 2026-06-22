"""Роуты Threads: auth status, auth url, reload, schedule, Selenium fallback."""

import asyncio
import base64
import json
import logging
import time

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional

from config import settings
from services.threads_service import (
    get_auth_status,
    build_oauth_url,
    get_pending_posts_for_user,
    set_post_status,
    verify_threads_auth,
)
from services.publish_service import publish_text_post, publish_image_post
from services.meta_selenium_login import run_meta_web_login
from services.selenium_diag_upload import upload_selenium_diagnostic_png
from services.selenium_session_service import (
    get_last_session,
    get_session_by_id,
    insert_session_running,
    update_session,
)

logger = logging.getLogger(__name__)

_selenium_last_attempt_ts: dict[int, float] = {}


class SeleniumAttemptBody(BaseModel):
    """Учётные данные только для одной попытки; не сохраняются в БД."""

    username: str = Field(..., min_length=1, max_length=512)
    password: str = Field(..., min_length=1, max_length=512)


def _selenium_rate_limit_ok(user_id: int) -> bool:
    now = time.time()
    last = _selenium_last_attempt_ts.get(user_id, 0.0)
    if now - last < float(settings.THREADS_SELENIUM_RATE_LIMIT_SECONDS):
        return False
    _selenium_last_attempt_ts[user_id] = now
    return True

router = APIRouter(prefix="/threads", tags=["Threads"])


def _get_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/auth/status/{user_id}")
async def auth_status(user_id: int):
    """Статус OAuth: connected, expires_at."""
    return await get_auth_status(user_id)


@router.get("/auth/verify/{user_id}")
async def auth_verify(user_id: int):
    """Проверка токена у Meta (debug_token или GET /me)."""
    return await verify_threads_auth(user_id)


@router.post("/selenium/attempt")
async def threads_selenium_attempt(
    body: SeleniumAttemptBody,
    x_user_id: Optional[str] = Header(None),
):
    """
    Диагностический веб-вход в Instagram через Selenium (не OAuth).
    Скрин в ответе (data URL) только при умеренном размере PNG; иначе только S3.
    """
    if not settings.ENABLE_THREADS_SELENIUM_FALLBACK:
        raise HTTPException(
            status_code=503,
            detail="Selenium fallback disabled (set ENABLE_THREADS_SELENIUM_FALLBACK=true)",
        )
    user_id = _get_user_id(x_user_id)
    if not _selenium_rate_limit_ok(user_id):
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Wait {settings.THREADS_SELENIUM_RATE_LIMIT_SECONDS}s.",
        )
    session_id = await insert_session_running(user_id)
    try:
        result = await asyncio.to_thread(
            run_meta_web_login,
            body.username,
            body.password,
            user_id,
            session_id,
        )
        status = result.get("status") or "failed"
        message = result.get("message") or ""
        png = result.get("diagnostic_png")
        diag_key = None
        if png:
            diag_key = await upload_selenium_diagnostic_png(user_id, session_id, png)
        detail = message
        if diag_key:
            detail = f"{message} | diagnostic_s3_key={diag_key}"
        await update_session(session_id, status, detail)
        max_b64 = int(settings.SELENIUM_DIAG_BASE64_MAX_BYTES)
        diagnostic_image_data_url: str | None = None
        if png and len(png) <= max_b64:
            b64 = base64.b64encode(png).decode("ascii")
            diagnostic_image_data_url = f"data:image/png;base64,{b64}"
        elif png:
            logger.info(
                "Selenium diagnostic PNG size %s exceeds base64 cap %s; S3 only",
                len(png),
                max_b64,
            )
        return {
            "session_id": session_id,
            "user_id": user_id,
            "status": status,
            "message": message,
            "diagnostic_s3_key": diag_key,
            "diagnostic_image_data_url": diagnostic_image_data_url,
            "disclaimer": "This does not grant Graph API OAuth. Use Connect with Threads for API publishing.",
        }
    except Exception as e:
        logger.exception("Selenium attempt failed")
        await update_session(session_id, "failed", str(e)[:500])
        raise HTTPException(status_code=500, detail="Selenium run failed") from e


@router.get("/selenium/session/last")
async def threads_selenium_session_last(x_user_id: Optional[str] = Header(None)):
    """Последняя запись диагностической сессии Selenium для пользователя."""
    user_id = _get_user_id(x_user_id)
    row = await get_last_session(user_id)
    if not row:
        return {"user_id": user_id, "session": None}
    return {"user_id": user_id, "session": row}


@router.get("/selenium/session/{session_id}")
async def threads_selenium_session_get(
    session_id: int,
    x_user_id: Optional[str] = Header(None),
):
    row = await get_session_by_id(session_id, _get_user_id(x_user_id))
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@router.get("/auth/url")
async def auth_url(x_user_id: Optional[str] = Header(None)):
    """URL для редиректа пользователя на Meta OAuth (state = user_id)."""
    user_id = _get_user_id(x_user_id)
    url = build_oauth_url(user_id)
    if not url:
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured (META_APP_ID, THREADS_OAUTH_REDIRECT_URI)",
        )
    return {"url": url}


@router.post("/reload")
async def reload():
    """Перезагрузка (заглушка: профили читаются из БД по запросу)."""
    return {"status": "ok", "message": "Reload done"}


@router.post("/schedule")
async def schedule():
    """
    Один проход: для каждого пользователя с publish_enabled и токеном
    забираем посты из threads_posts и публикуем в Threads API.
    """
    from database import get_db_connection, release_db_connection

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, access_token, threads_user_id
                FROM threads_profiles
                WHERE publish_enabled = TRUE AND access_token IS NOT NULL AND access_token != ''
                """
            )
            rows = await cur.fetchall()
    finally:
        release_db_connection(conn)

    published = 0
    errors = 0
    for (user_id, access_token, threads_user_id) in rows:
        if not threads_user_id:
            logger.warning("user_id=%s: threads_user_id not set, skip publish", user_id)
            continue
        posts = await get_pending_posts_for_user(user_id, limit=5)
        for post in posts:
            post_id = post["id"]
            text = (post.get("post_text") or "").strip()
            raw_images = post.get("images") or []
            images = raw_images if isinstance(raw_images, list) else (json.loads(raw_images) if isinstance(raw_images, str) else [])
            if not text:
                await set_post_status(user_id, post_id, "skipped")
                continue
            if images:
                # Публикуем с первым изображением (URL должен быть абсолютным и доступным для Meta)
                img_url = images[0] if isinstance(images[0], str) else images[0]
                result = await publish_image_post(
                    threads_user_id, access_token, text, img_url
                )
            else:
                result = await publish_text_post(threads_user_id, access_token, text)
            if result:
                await set_post_status(user_id, post_id, "published")
                published += 1
            else:
                await set_post_status(user_id, post_id, "failed")
                errors += 1

    return {"status": "ok", "published": published, "errors": errors}

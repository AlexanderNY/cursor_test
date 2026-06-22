"""Роутер для Threads (Meta) профилей и постов."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import RedirectResponse, FileResponse
import uuid
import httpx

from services.profile_service import profile_service
from services.post_service import post_service
from schemas import ThreadsProfileCreate
from storage_client import get_storage
from config import settings


router = APIRouter(prefix="/threads", tags=["Threads"])

UPLOADS_THREADS_DIR = Path("uploads/threads")
S3_KEY_PREFIX = "uploads/threads"


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/profile")
async def get_threads_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль Threads пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_threads_profile(user_id)
    if profile:
        return profile
    return {
        "instagram_handle": None,
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "process_enabled": False,
        "processing_description": None,
        "remove_emojis": False,
        "remove_images": False,
        "clean_html": False,
        "process_services": [],
        "status_review_after_process": False,
        "add_static_html": False,
        "static_html_content": None,
        "threads_connected": False,
        "threads_user_id": None,
    }


@router.post("/profile")
async def save_threads_profile(
    data: ThreadsProfileCreate,
    x_user_id: Optional[str] = Header(None),
):
    """Сохраняет профиль Threads пользователя (без токенов)."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_threads_profile(user_id, data.model_dump())
    return profile


@router.get("/profiles")
async def get_all_threads_profiles():
    """Получает все профили Threads (для админки)."""
    profiles = await profile_service.get_all_threads_profiles()
    return {"profiles": profiles}


@router.post("/post")
async def create_threads_post(
    text: str = Form(..., max_length=500),
    image: Optional[UploadFile] = File(None),
    to_tg: bool = Form(False),
    to_tw: bool = Form(False),
    to_wp: bool = Form(False),
    to_vk: bool = Form(False),
    to_threads: bool = Form(True),
    x_user_id: Optional[str] = Header(None),
):
    """Создает пост для Threads (max 500 символов) с поддержкой изображений. Файлы — в S3 или локально."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        images = []
        if image:
            content = await image.read()
            file_extension = Path(image.filename).suffix if image.filename else ".jpg"
            file_name = f"{uuid.uuid4()}{file_extension}"
            storage = get_storage()
            if storage:
                key = f"{S3_KEY_PREFIX}/{file_name}"
                await storage.put(key, content)
                image_url = f"/uploads/threads/{file_name}"
            else:
                UPLOADS_THREADS_DIR.mkdir(parents=True, exist_ok=True)
                (UPLOADS_THREADS_DIR / file_name).write_bytes(content)
                image_url = f"/uploads/threads/{file_name}"
            images.append(image_url)
        post = await post_service.create_threads_post_record(
            user_id=user_id,
            text=text,
            images=images if images else None,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts")
async def get_threads_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов Threads пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_threads_posts(user_id=user_id, limit=limit, offset=offset)
    return posts


@router.get("/post/{post_id}")
async def get_threads_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост Threads по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_threads_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_threads_post(
    post_id: int,
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост Threads."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        images = None
        if image:
            content = await image.read()
            file_extension = Path(image.filename).suffix if image.filename else ".jpg"
            file_name = f"{uuid.uuid4()}{file_extension}"
            storage = get_storage()
            if storage:
                key = f"{S3_KEY_PREFIX}/{file_name}"
                await storage.put(key, content)
            else:
                UPLOADS_THREADS_DIR.mkdir(parents=True, exist_ok=True)
                (UPLOADS_THREADS_DIR / file_name).write_bytes(content)
            images = [f"/uploads/threads/{file_name}"]
        post = await post_service.update_threads_post(
            user_id=user_id,
            post_id=post_id,
            text=text,
            images=images,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_threads_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост Threads как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_threads_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/oauth/callback")
async def threads_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """OAuth callback от Meta: обмен code на token и редирект в UI."""
    frontend_url = (settings.FRONTEND_URL or "").rstrip("/")
    threads_page = f"{frontend_url}/threads"
    if error:
        return RedirectResponse(url=f"{threads_page}?oauth=error&message={error}")
    if not code or not state:
        return RedirectResponse(url=f"{threads_page}?oauth=error&message=missing_code_or_state")
    try:
        user_id = int(state)
    except (ValueError, TypeError):
        return RedirectResponse(url=f"{threads_page}?oauth=error&message=invalid_state")
    app_id = getattr(settings, "META_APP_ID", None) or ""
    app_secret = getattr(settings, "META_APP_SECRET", None) or ""
    redirect_uri = getattr(settings, "THREADS_OAUTH_REDIRECT_URI", None) or ""
    if not app_id or not app_secret or not redirect_uri:
        return RedirectResponse(url=f"{threads_page}?oauth=error&message=server_config")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, Exception) as e:
            return RedirectResponse(url=f"{threads_page}?oauth=error&message=exchange_failed")
    access_token = data.get("access_token")
    if not access_token:
        return RedirectResponse(url=f"{threads_page}?oauth=error&message=no_token")
    expires_in = data.get("expires_in")
    token_expires_at = None
    if expires_in is not None:
        from datetime import datetime, timedelta
        token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
    await profile_service.save_threads_oauth_tokens(
        user_id=user_id,
        access_token=access_token,
        refresh_token=data.get("refresh_token"),
        token_expires_at=token_expires_at,
        threads_user_id=None,
    )
    return RedirectResponse(url=f"{threads_page}?oauth=success")

"""Роутер для Telegram профилей и постов."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import FileResponse, RedirectResponse

from services.profile_service import profile_service
from services.post_service import post_service
from services.platform_auth_service import (
    PlatformAction,
    PlatformAuthError,
    platform_auth_service,
    platform_auth_http_detail,
)
from services.tg_analytics_service import tg_analytics_service
from schemas import TelegramProfileCreate, TgPostTemplateCreate
from storage_client import get_storage
from shared import async_fs


router = APIRouter(prefix="/tg", tags=["Telegram"])

UPLOADS_TG_DIR = Path("uploads/tg")
S3_KEY_PREFIX = "uploads/tg"


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса.
    
    Args:
        x_user_id: ID пользователя из заголовка
        
    Returns:
        int: ID пользователя
        
    Raises:
        HTTPException: Если заголовок отсутствует или невалиден
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/profile")
async def get_tg_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль Telegram пользователя.
    
    Returns:
        Профиль Telegram или пустой объект
    """
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_tg_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "api_id": None,
        "api_hash": None,
        "telegram_username": None,
        "auth_phone_number": None,
        "chats_to_read": [],
        "save_conditions": [],
        "channel_to_post": None,
        "channels_to_post": [],
        "process_enabled": False,
        "processing_description": None,
        "remove_emojis": False,
        "remove_images": False,
        "clean_html": False,
        "process_services": [],
        "status_review_after_process": False,
        "add_static_html": False,
        "static_html_content": None,
        "alert_enabled": False,
        "alert_rules": [],
        "summarize_enabled": False,
        "summarize_min_length": 500,
        "digest_interval_min": 30,
        "digest_channel": None,
        "classification_enabled": False,
        "classification_categories": ["новости", "реклама", "технологии", "финансы", "другое"],
    }


@router.post("/profile")
async def save_tg_profile(
    data: TelegramProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль Telegram пользователя.
    
    Args:
        data: Данные профиля
    
    Returns:
        Сохраненный профиль
    """
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_tg_profile(user_id, data.model_dump())
    return profile


@router.get("/profiles")
async def get_all_tg_profiles():
    """Получает все профили Telegram.
    
    Returns:
        Список всех профилей Telegram
    """
    profiles = await profile_service.get_all_tg_profiles()
    return {"profiles": profiles}


@router.post("/post")
async def create_tg_post(
    text: str = Form(..., max_length=4096),
    image: Optional[UploadFile] = File(None),
    to_tg: bool = Form(True),
    to_tw: bool = Form(False),
    to_wp: bool = Form(False),
    to_vk: bool = Form(False),
    to_threads: bool = Form(False),
    to_dzen: bool = Form(False),
    to_instagram: bool = Form(False),
    publish_at: Optional[str] = Form(None),
    target_channels: Optional[str] = Form(None),
    target_groups: Optional[str] = Form(None),
    x_user_id: Optional[str] = Header(None)
):
    """Создает пост для Telegram (max 4096 символов) с поддержкой изображений.
    
    Args:
        text: Текст поста
        image: Опциональное изображение
        publish_at: ISO datetime для отложенной публикации
        target_channels: JSON-массив каналов
        target_groups: JSON-массив VK-групп
        
    Returns:
        Созданный пост
    """
    user_id = get_user_id_from_header(x_user_id)

    if to_tg:
        try:
            await platform_auth_service.require_platform(
                user_id, "tg", PlatformAction.PUBLISH_TEXT
            )
        except PlatformAuthError as exc:
            raise HTTPException(status_code=403, detail=platform_auth_http_detail(exc))

    try:
        images = []
        if image:
            content = await image.read()
            file_extension = Path(image.filename).suffix if image.filename else ".jpg"
            file_name = f"{uuid.uuid4()}{file_extension}"
            storage = get_storage()
            if storage:
                await storage.put(f"{S3_KEY_PREFIX}/{file_name}", content)
            else:
                await async_fs.makedirs(UPLOADS_TG_DIR)
                await async_fs.write_bytes(UPLOADS_TG_DIR / file_name, content)
            image_url = f"/uploads/tg/{file_name}"
            images.append(image_url)

        def _parse_id_list(raw: Optional[str]) -> Optional[list]:
            if not raw:
                return None
            import json as _json
            try:
                parsed = _json.loads(raw)
                if isinstance(parsed, list):
                    return [str(c).strip() for c in parsed if str(c).strip()]
            except (_json.JSONDecodeError, TypeError):
                return [c.strip() for c in raw.split(",") if c.strip()]
            return None

        channels = _parse_id_list(target_channels)
        groups = _parse_id_list(target_groups)
        
        post = await post_service.create_tg_post_record(
            user_id=user_id,
            text=text,
            images=images if images else None,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            publish_at=publish_at or None,
            target_channels=channels,
            target_groups=groups,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts")
async def get_tg_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Возвращает список постов Telegram пользователя из таблицы tg_posts."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_tg_posts(
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return posts


@router.get("/post/{post_id}")
async def get_tg_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост Telegram по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_tg_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_tg_post(
    post_id: int,
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    publish_at: Optional[str] = Form(None),
    clear_publish_at: bool = Form(False),
    target_channels: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост Telegram."""
    user_id = get_user_id_from_header(x_user_id)
    
    try:
        images = None
        if image:
            content = await image.read()
            file_extension = Path(image.filename).suffix if image.filename else ".jpg"
            file_name = f"{uuid.uuid4()}{file_extension}"
            storage = get_storage()
            if storage:
                await storage.put(f"{S3_KEY_PREFIX}/{file_name}", content)
            else:
                await async_fs.makedirs(UPLOADS_TG_DIR)
                await async_fs.write_bytes(UPLOADS_TG_DIR / file_name, content)
            image_url = f"/uploads/tg/{file_name}"
            images = [image_url]

        channels = None
        if target_channels is not None:
            import json as _json
            try:
                parsed = _json.loads(target_channels)
                if isinstance(parsed, list):
                    channels = [str(c).strip() for c in parsed if str(c).strip()]
                else:
                    channels = []
            except (_json.JSONDecodeError, TypeError):
                channels = [c.strip() for c in target_channels.split(",") if c.strip()]
        
        post = await post_service.update_tg_post(
            user_id=user_id,
            post_id=post_id,
            text=text,
            images=images,
            status=status,
            publish_at=None if clear_publish_at else (publish_at or None),
            clear_publish_at=clear_publish_at,
            target_channels=channels,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/post/{post_id}/approve")
async def approve_tg_post(
    post_id: int,
    publish_at: Optional[str] = Form(None),
    x_user_id: Optional[str] = Header(None),
):
    """Approve review post → ready (+ optional publish_at)."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        await platform_auth_service.require_platform(
            user_id, "tg", PlatformAction.PUBLISH_TEXT
        )
    except PlatformAuthError as exc:
        raise HTTPException(status_code=403, detail=platform_auth_http_detail(exc))
    post = await post_service.approve_tg_post(user_id, post_id, publish_at=publish_at or None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/post/{post_id}")
async def delete_tg_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост Telegram как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_tg_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/templates")
async def list_tg_templates(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id_from_header(x_user_id)
    return await post_service.list_tg_templates(user_id)


@router.post("/templates")
async def create_tg_template(
    data: TgPostTemplateCreate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await post_service.create_tg_template(
        user_id, data.name, data.text, data.hashtags
    )


@router.delete("/templates/{template_id}")
async def delete_tg_template(
    template_id: int,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    ok = await post_service.delete_tg_template(user_id, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True}


@router.get("/uploads/{filename}")
async def get_tg_upload(filename: str):
    """Отдаёт файл: редирект на presigned URL (S3) или FileResponse с локального диска."""
    if "/" in filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    storage = get_storage()
    if storage:
        key = f"{S3_KEY_PREFIX}/{filename}"
        url = await storage.get_presigned_url(key, expires_in=3600)
        if url:
            return RedirectResponse(url=url, status_code=302)
        raise HTTPException(status_code=404, detail="File not found")
    file_path = UPLOADS_TG_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@router.get("/analytics/overview")
async def get_tg_analytics_overview(
    period: str = "7d",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_overview(user_id, period)


@router.get("/analytics/channels")
async def get_tg_analytics_channels(
    period: str = "7d",
    limit: int = 10,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_channels(user_id, period, limit)


@router.get("/analytics/keywords")
async def get_tg_analytics_keywords(
    period: str = "7d",
    limit: int = 20,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_keywords(user_id, period, limit)


@router.get("/analytics/alerts")
async def get_tg_analytics_alerts(
    period: str = "7d",
    limit: int = 50,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_alerts(user_id, period, limit)


@router.get("/analytics/timeline")
async def get_tg_analytics_timeline(
    period: str = "7d",
    granularity: str = "hour",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_timeline(user_id, period, granularity)


@router.get("/analytics/sentiment")
async def get_tg_analytics_sentiment(
    period: str = "7d",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_sentiment_breakdown(user_id, period)


@router.get("/analytics/engagement")
async def get_tg_analytics_engagement(
    period: str = "7d",
    limit: int = 10,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id_from_header(x_user_id)
    return await tg_analytics_service.get_engagement(user_id, period, limit)

"""Роутер для Telegram профилей и постов."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import FileResponse, RedirectResponse

from services.profile_service import profile_service
from services.post_service import post_service
from schemas import TelegramProfileCreate
from storage_client import get_storage


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
    x_user_id: Optional[str] = Header(None)
):
    """Создает пост для Telegram (max 4096 символов) с поддержкой изображений.
    
    Args:
        text: Текст поста
        image: Опциональное изображение
        
    Returns:
        Созданный пост
    """
    user_id = get_user_id_from_header(x_user_id)
    
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
                UPLOADS_TG_DIR.mkdir(parents=True, exist_ok=True)
                (UPLOADS_TG_DIR / file_name).write_bytes(content)
            image_url = f"/uploads/tg/{file_name}"
            images.append(image_url)
        
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
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts")
async def get_tg_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов Telegram пользователя из таблицы tg_posts.
    
    Args:
        x_user_id: ID пользователя из заголовка
        limit: Максимальное количество записей
        offset: Смещение для постраничной загрузки
    
    Returns:
        Список постов Telegram
    """
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_tg_posts(user_id=user_id, limit=limit, offset=offset)
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
                UPLOADS_TG_DIR.mkdir(parents=True, exist_ok=True)
                (UPLOADS_TG_DIR / file_name).write_bytes(content)
            image_url = f"/uploads/tg/{file_name}"
            images = [image_url]
        
        post = await post_service.update_tg_post(
            user_id=user_id,
            post_id=post_id,
            text=text,
            images=images
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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

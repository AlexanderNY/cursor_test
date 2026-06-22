"""Роутер для Instagram: профили и посты."""

import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form
from services.profile_service import profile_service
from services.post_service import post_service
from schemas import InstagramProfileCreate, InstagramPost, InstagramPostUpdate
from storage_client import get_storage


router = APIRouter(prefix="/instagram", tags=["Instagram"])

S3_KEY_PREFIX = "uploads/instagram"


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


async def _save_upload(upload_dir: Path, file: UploadFile, subdir: str) -> str:
    """Сохраняет загруженный файл в S3 или локально. Возвращает относительный URL (/uploads/instagram/...)."""
    ext = Path(file.filename).suffix if file.filename else ".bin"
    name = f"{uuid.uuid4()}{ext}"
    content = await file.read()
    storage = get_storage()
    if storage:
        key = f"{S3_KEY_PREFIX}/{subdir}/{name}"
        await storage.put(key, content)
        return f"/uploads/instagram/{subdir}/{name}"
    target = upload_dir / subdir
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    path.write_bytes(content)
    return f"/uploads/instagram/{subdir}/{name}"


@router.get("/profile")
async def get_instagram_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль Instagram пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_instagram_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "username": None,
        "password": None,
        "usernames_to_read": [],
        "process_enabled": False,
        "processing_description": None,
        "remove_emojis": False,
        "remove_images": False,
        "clean_html": False,
        "process_services": None,
        "status_review_after_process": False,
        "add_static_html": False,
        "static_html_content": None,
        "instagram_verification_code": None,
        "instagram_last_auth_error": None,
        "instagram_verification_pending": False,
        "has_instagram_session": False,
    }


@router.post("/profile")
async def save_instagram_profile(
    data: InstagramProfileCreate,
    x_user_id: Optional[str] = Header(None),
):
    """Сохраняет профиль Instagram пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_instagram_profile(user_id, data.model_dump())
    return profile


@router.get("/profiles")
async def get_all_instagram_profiles():
    """Получает все профили Instagram."""
    profiles = await profile_service.get_all_instagram_profiles()
    return {"profiles": profiles}


@router.get("/posts")
async def get_instagram_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов Instagram пользователя из таблицы instagram_posts."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_instagram_posts(user_id=user_id, limit=limit, offset=offset)
    return posts


@router.post("/post")
async def create_instagram_post(
    data: Optional[InstagramPost] = None,
    caption: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    x_user_id: Optional[str] = Header(None),
):
    """Создает пост Instagram (caption max 2200 символов). Поддержка JSON или multipart с загрузкой изображений."""
    user_id = get_user_id_from_header(x_user_id)
    upload_dir = Path("uploads/instagram")

    if data is not None:
        post_caption = data.caption
        images_list = list(data.images or [])
        to_tg = data.to_tg
        to_tw = data.to_tw
        to_wp = data.to_wp
        to_vk = data.to_vk
        to_dzen = data.to_dzen
        to_threads = data.to_threads
        to_instagram = data.to_instagram
    else:
        if caption is None:
            raise HTTPException(status_code=400, detail="caption or data body required")
        post_caption = caption
        images_list = []
        to_tg = to_tw = to_wp = to_vk = to_dzen = to_threads = False
        to_instagram = True

    try:
        for img in images or []:
            if img.filename:
                url = await _save_upload(upload_dir, img, "images")
                images_list.append(url)
        post = await post_service.create_instagram_post_record(
            user_id=user_id,
            caption=post_caption,
            images=images_list if images_list else None,
            videos=None,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_dzen=to_dzen,
            to_threads=to_threads,
            to_instagram=to_instagram,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/post/{post_id}")
async def get_instagram_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост Instagram по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_instagram_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_instagram_post(
    post_id: int,
    data: InstagramPostUpdate,
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост Instagram."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        post = await post_service.update_instagram_post(
            user_id=user_id,
            post_id=post_id,
            caption=data.caption,
            images=data.images,
            status=data.status,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_instagram_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост Instagram как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_instagram_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

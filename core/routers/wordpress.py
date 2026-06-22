"""Роутер для WordPress профилей и постов."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from services.profile_service import profile_service
from services.post_service import post_service
from schemas import (
    WordPressProfileCreate,
    WordPressPublishProfileCreate,
    WordPressCollectProfileCreate,
    WordPressPost,
)


router = APIRouter(prefix="/wp", tags=["WordPress"])


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/profile")
async def get_wp_profile(x_user_id: Optional[str] = Header(None)):
    """Получает объединенный профиль WordPress (publish + collect) для обратной совместимости."""
    user_id = get_user_id_from_header(x_user_id)
    pub = await profile_service.get_wp_publish_profile(user_id)
    coll = await profile_service.get_wp_collect_profile(user_id)
    result = {
        "publish_enabled": pub.get("publish_enabled", False) if pub else False,
        "collect_enabled": coll.get("collect_enabled", False) if coll else False,
        "schedule_type": (pub or {}).get("schedule_type", "on_new_messages"),
        "time_intervals": (pub or {}).get("time_intervals") or "",
        "site_url": (pub or {}).get("site_url"),
        "username": (pub or {}).get("username"),
        "app_password": (pub or {}).get("app_password"),
    }
    if coll and coll.get("collect_sites") is not None:
        result["collect_sites"] = coll["collect_sites"]
    return result


@router.post("/profile")
async def save_wp_profile(
    data: WordPressProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль WordPress (legacy: сохраняет в оба профиля publish и collect)."""
    user_id = get_user_id_from_header(x_user_id)
    d = data.model_dump()
    ti = d.get("time_intervals")
    if isinstance(ti, str):
        time_intervals_val = ti
    elif isinstance(ti, list) and len(ti) > 0 and isinstance(ti[0], dict) and ti[0].get("start"):
        time_intervals_val = ti[0]["start"]
    else:
        time_intervals_val = ""
    await profile_service.save_wp_publish_profile(user_id, {
        "publish_enabled": d.get("publish_enabled", False),
        "schedule_type": d.get("schedule_type", "on_new_messages"),
        "time_intervals": time_intervals_val,
        "site_url": d.get("site_url"),
        "username": d.get("username"),
        "app_password": d.get("app_password"),
    })
    await profile_service.save_wp_collect_profile(user_id, {
        "collect_enabled": d.get("collect_enabled", False),
        "collect_sites": d.get("collect_sites", []),
    })
    return await get_wp_profile(x_user_id)


# --- Publish profile (Post Profile Settings) ---

@router.get("/publish-profile")
async def get_wp_publish_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль публикации WordPress пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_wp_publish_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "schedule_type": "on_new_messages",
        "time_intervals": "",
        "site_url": None,
        "username": None,
        "app_password": None,
    }


@router.post("/publish-profile")
async def save_wp_publish_profile(
    data: WordPressPublishProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль публикации WordPress."""
    user_id = get_user_id_from_header(x_user_id)
    return await profile_service.save_wp_publish_profile(user_id, data.model_dump(exclude_none=True))


# --- Collect profile (Parser Profile Settings) ---

@router.get("/collect-profile")
async def get_wp_collect_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль сбора (parser) WordPress пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_wp_collect_profile(user_id)
    if profile:
        return profile
    return {
        "collect_enabled": False,
        "collect_sites": [],
    }


@router.post("/collect-profile")
async def save_wp_collect_profile(
    data: WordPressCollectProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль сбора WordPress."""
    user_id = get_user_id_from_header(x_user_id)
    return await profile_service.save_wp_collect_profile(user_id, data.model_dump(exclude_none=True))


@router.get("/profiles")
async def get_all_wp_profiles():
    """Получает все профили WordPress.
    
    Returns:
        Список всех профилей WordPress
    """
    profiles = await profile_service.get_all_wp_profiles()
    return {"profiles": profiles}


@router.get("/posts")
async def get_wp_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов WordPress пользователя из таблицы wp_posts.
    
    Args:
        x_user_id: ID пользователя из заголовка
        limit: Максимальное количество записей
        offset: Смещение для постраничной загрузки
    
    Returns:
        Список постов WordPress
    """
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_wp_posts(user_id=user_id, limit=limit, offset=offset)
    return posts


@router.get("/post/{post_id}")
async def get_wp_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост WordPress по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_wp_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/post")
async def create_wp_post(
    data: WordPressPost,
    x_user_id: Optional[str] = Header(None)
):
    """Создает пост WordPress в таблице wp_posts.
    
    Args:
        data: Данные поста в формате ui-app (реальный WordPress)
        
    Returns:
        Созданный пост
    """
    user_id = get_user_id_from_header(x_user_id)
    
    try:
        post = await post_service.create_wp_post_record(
            user_id=user_id,
            text=data.post.content,
            title=data.post.title,
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


@router.put("/post/{post_id}")
async def update_wp_post(
    post_id: int,
    data: WordPressPost,
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост WordPress."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.update_wp_post(
        user_id=user_id,
        post_id=post_id,
        title=data.post.title,
        post_text=data.post.content,
        status=data.post.status,
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/post/{post_id}")
async def delete_wp_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост WordPress как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_wp_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

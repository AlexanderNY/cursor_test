"""Роутер для ручных постов (cPost)."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from services.profile_service import profile_service
from services.post_service import post_service
from schemas import CpostProfileCreate, CpostPost, CpostPostUpdate


router = APIRouter(prefix="/cpost", tags=["Manual Posts"])


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/profile")
async def get_cpost_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль ручных постов пользователя.
    
    Returns:
        Профиль или пустой объект
    """
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_cpost_profile(user_id)
    if profile:
        return profile
    return {
        "default_platforms": {
            "tg": False,
            "tw": False,
            "wp": False,
            "vk": False,
            "threads": False,
            "dzen": False,
            "instagram": False,
        }
    }


@router.post("/profile")
async def save_cpost_profile(
    data: CpostProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль ручных постов пользователя.
    
    Args:
        data: Данные профиля
        
    Returns:
        Сохраненный профиль
    """
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_cpost_profile(user_id, data.model_dump())
    return profile


@router.post("/post")
async def create_manual_post(
    data: CpostPost,
    x_user_id: Optional[str] = Header(None)
):
    """Создает ручной пост (max 150000 символов).
    
    Args:
        data: Данные поста
        
    Returns:
        Созданный пост
    """
    user_id = get_user_id_from_header(x_user_id)
    
    try:
        post = await post_service.create_cpost_post_record(
            user_id=user_id,
            text=data.text,
            title=data.title,
            to_tg=data.to_tg,
            to_tw=data.to_tw,
            to_wp=data.to_wp,
            to_vk=data.to_vk,
            to_threads=data.to_threads,
            to_dzen=data.to_dzen,
            to_instagram=data.to_instagram,
            status=data.status,
            domain=data.domain,
            url=data.url,
            author=data.author,
            avatar=data.avatar,
            post_date=data.post_date,
            screenshot=data.screenshot,
            images=data.images,
            image_over_text=data.image_over_text,
            comments=data.comments,
            reposts=data.reposts,
            likes=data.likes,
            views=data.views,
            is_ad=data.is_ad,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts")
async def get_cpost_posts(
    limit: int = 50,
    offset: int = 0,
    x_user_id: Optional[str] = Header(None)
):
    """Возвращает список ручных постов из cpost_posts."""
    user_id = get_user_id_from_header(x_user_id)
    return await post_service.get_cpost_posts(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/post/{post_id}")
async def get_cpost_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None)
):
    """Возвращает один ручной пост по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_cpost_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_cpost_post(
    post_id: int,
    data: CpostPostUpdate,
    x_user_id: Optional[str] = Header(None)
):
    """Обновляет ручной пост."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.update_cpost_post(
        user_id=user_id,
        post_id=post_id,
        title=data.title,
        post_text=data.text,
        to_tg=data.to_tg,
        to_tw=data.to_tw,
        to_wp=data.to_wp,
        to_vk=data.to_vk,
        to_threads=data.to_threads,
        to_dzen=data.to_dzen,
        to_instagram=data.to_instagram,
        domain=data.domain,
        url=data.url,
        author=data.author,
        avatar=data.avatar,
        post_date=data.post_date,
        screenshot=data.screenshot,
        images=data.images,
        image_over_text=data.image_over_text,
        comments=data.comments,
        reposts=data.reposts,
        likes=data.likes,
        views=data.views,
        is_ad=data.is_ad,
        status=data.status,
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/post/{post_id}")
async def delete_cpost_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None)
):
    """Удаляет ручной пост."""
    user_id = get_user_id_from_header(x_user_id)
    deleted = await post_service.delete_cpost_post(user_id=user_id, post_id=post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True}

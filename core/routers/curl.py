"""Роутер для cURL настроек скрапинга и сохранения постов из url-bot."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from schemas import CurlOneTimeDoneRequest, CurlSettingsCreate, UrlPostsBatchRequest
from services.profile_service import profile_service
from services.post_service import post_service
from services.url_posts_service import save_url_posts_batch

router = APIRouter(prefix="/curl", tags=["cURL"])


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/settings")
async def get_curl_settings(x_user_id: Optional[str] = Header(None)):
    """Получает настройки cURL скрапинга пользователя.
    
    Returns:
        Настройки cURL или пустой объект
    """
    user_id = get_user_id_from_header(x_user_id)
    settings = await profile_service.get_curl_settings(user_id)
    if settings:
        return settings
    return {
        "collect_enabled": False,
        "urls": [],
        "process_before_publish": False,
        "process_description": None,
        "remove_emojis": False,
        "remove_images": False,
        "clean_html": False,
        "process_services": [],
        "status_review_after_process": False,
        "add_static_html": False,
        "static_html_content": None,
        "screenshot_only": False,
    }


@router.post("/settings")
async def save_curl_settings(
    data: CurlSettingsCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет настройки cURL скрапинга пользователя.
    
    Args:
        data: Данные настроек
        
    Returns:
        Сохраненные настройки
    """
    user_id = get_user_id_from_header(x_user_id)
    settings = await profile_service.save_curl_settings(user_id, data.model_dump())
    return settings


@router.get("/posts")
async def get_curl_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов из url_posts пользователя (собранные по URL)."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_url_posts(user_id=user_id, limit=limit, offset=offset)
    return posts


@router.post("/url-posts")
async def save_url_posts_batch_endpoint(
    body: UrlPostsBatchRequest,
    x_user_id: Optional[str] = Header(None),
):
    """
    Сохраняет пакет постов из url-bot в таблицу url_posts.

    Вызывается scheduler после получения ответа от url-bot /schedule.
    Для каждого поста: при screenshot_path путь сохраняется в images;
    при screenshot_base64 — файл сохраняется в uploads/url/..., в images — путь.
    """
    items = [p.model_dump() for p in body.posts]
    if not items:
        return {"saved": 0, "ids": []}
    ids = await save_url_posts_batch(items)
    return {"saved": len(ids), "ids": ids}


@router.post("/one-time-done")
async def curl_one_time_done(body: CurlOneTimeDoneRequest):
    """
    Отмечает одноразовые URL как выполненные (вызывается scheduler после успешного run_once).
    """
    items = [p.model_dump() for p in body.items]
    await profile_service.record_curl_one_time_done_batch(items)
    return {"recorded": len(items)}

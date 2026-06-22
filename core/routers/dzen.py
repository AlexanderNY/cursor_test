"""Роутер для Яндекс Дзен: профили, посты и RSS-лента."""

import html
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form, Query
from fastapi.responses import Response
from services.profile_service import profile_service
from services.post_service import post_service
from schemas import DzenProfileCreate, DzenPost, DzenPostUpdate
from database import get_db_connection, release_db_connection
from config import settings
from storage_client import get_storage


router = APIRouter(prefix="/dzen", tags=["Dzen"])

S3_KEY_PREFIX = "uploads/dzen"


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


async def _save_upload(upload_dir: Path, file: UploadFile, subdir: str) -> str:
    """Сохраняет загруженный файл в S3 или локально. Возвращает относительный URL (/uploads/dzen/...)."""
    ext = Path(file.filename).suffix if file.filename else ".bin"
    name = f"{uuid.uuid4()}{ext}"
    content = await file.read()
    storage = get_storage()
    if storage:
        key = f"{S3_KEY_PREFIX}/{subdir}/{name}"
        await storage.put(key, content)
        return f"/uploads/dzen/{subdir}/{name}"
    target = upload_dir / subdir
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    path.write_bytes(content)
    return f"/uploads/dzen/{subdir}/{name}"


@router.get("/profile")
async def get_dzen_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль Дзен пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_dzen_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "rss_feed_url": None,
        "channel_name": None,
        "channels_to_read": [],
        "rss_token": None,
        "yandex_login": None,
        "yandex_password": None,
        "dzen_studio_url": None,
        "collect_source": "rss",
        "last_auth_error": None,
    }


@router.post("/profile")
async def save_dzen_profile(
    data: DzenProfileCreate,
    x_user_id: Optional[str] = Header(None),
):
    """Сохраняет профиль Дзен пользователя."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.save_dzen_profile(user_id, data.model_dump())
    return profile


@router.get("/profiles")
async def get_all_dzen_profiles():
    """Получает все профили Дзен."""
    profiles = await profile_service.get_all_dzen_profiles()
    return {"profiles": profiles}


@router.get("/posts")
async def get_dzen_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
):
    """Возвращает список постов Дзен пользователя из таблицы dzen_posts."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_dzen_posts(user_id=user_id, limit=limit, offset=offset)
    return posts


@router.post("/post")
async def create_dzen_post(
    data: Optional[DzenPost] = None,
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[]),
    x_user_id: Optional[str] = Header(None),
):
    """Создает пост Дзен (max 1500 символов). Поддержка JSON или multipart с загрузкой изображений и видео."""
    user_id = get_user_id_from_header(x_user_id)
    upload_dir = Path("uploads/dzen")

    if data is not None:
        # JSON body
        post_text = data.text
        post_title = data.title
        images_list = list(data.images or [])
        videos_list = list(data.videos or [])
        to_tg = data.to_tg
        to_tw = data.to_tw
        to_wp = data.to_wp
        to_vk = data.to_vk
        to_dzen = data.to_dzen
        to_threads = data.to_threads
        to_instagram = data.to_instagram
    else:
        if text is None:
            raise HTTPException(status_code=400, detail="text or data body required")
        post_text = text
        post_title = title
        images_list = []
        videos_list = []
        to_tg = to_tw = to_wp = to_vk = False
        to_dzen = True
        to_threads = False
        to_instagram = False

    try:
        for img in images or []:
            if img.filename:
                url = await _save_upload(upload_dir, img, "images")
                images_list.append(url)
        for vid in videos or []:
            if vid.filename:
                url = await _save_upload(upload_dir, vid, "videos")
                videos_list.append(url)
        post = await post_service.create_dzen_post_record(
            user_id=user_id,
            text=post_text,
            title=post_title,
            images=images_list if images_list else None,
            videos=videos_list if videos_list else None,
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
async def get_dzen_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост Дзен по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_dzen_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_dzen_post(
    post_id: int,
    data: DzenPostUpdate,
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост Дзен."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        post = await post_service.update_dzen_post(
            user_id=user_id,
            post_id=post_id,
            text=data.text,
            title=data.title,
            images=data.images,
            videos=data.videos,
            status=data.status,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_dzen_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост Дзен как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_dzen_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def _rfc822_date(dt: Optional[datetime]) -> str:
    """Форматирует дату в RFC-822 для RSS."""
    if not dt:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def _escape_xml(s: str) -> str:
    """Экранирует символы для XML."""
    if not s:
        return ""
    return html.escape(s, quote=True)


async def _build_dzen_rss_xml(user_id: int, channel_title: str, base_url: str, posts: List[dict]) -> str:
    """Собирает RSS 2.0 XML по спецификации Дзена (yandex:full-text, enclosure, media:group)."""
    channel_title_esc = _escape_xml(channel_title or "Dzen Channel")
    link_esc = _escape_xml(base_url.rstrip("/"))
    items_xml = []
    for p in posts:
        post_id = p.get("id")
        title = (p.get("title") or p.get("post_text") or "")[:200]
        title_esc = _escape_xml(title.strip() or "Без заголовка")
        item_link = f"{base_url}/dzen/article/{user_id}/{post_id}"
        link_esc_item = _escape_xml(item_link)
        post_text = p.get("post_text") or ""
        full_text_esc = _escape_xml(post_text)
        pub_date = _rfc822_date(p.get("post_date"))
        images = p.get("images") or []
        if isinstance(images, str):
            try:
                images = json.loads(images)
            except (json.JSONDecodeError, TypeError):
                images = []
        videos = p.get("videos") or []
        if isinstance(videos, str):
            try:
                videos = json.loads(videos)
            except (json.JSONDecodeError, TypeError):
                videos = []

        enclosures = []
        for url in images:
            if isinstance(url, dict):
                url = url.get("url") or url.get("src") or ""
            if url:
                enclosures.append(f'<enclosure url="{_escape_xml(str(url))}" type="image/jpeg"/>')
        for url in videos:
            if isinstance(url, dict):
                url = url.get("url") or ""
            if url:
                enclosures.append(
                    f'<media:group><media:content url="{_escape_xml(str(url))}" type="video/mp4"/>'
                    f'<media:thumbnail url="{_escape_xml(str(url))}"/></media:group>'
                )

        items_xml.append(
            f"""<item>
<title>{title_esc}</title>
<link>{link_esc_item}</link>
<pubDate>{pub_date}</pubDate>
<yandex:full-text>{full_text_esc}</yandex:full-text>
{"".join(enclosures)}
</item>"""
        )

    items_str = "\n".join(items_xml)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:yandex="http://news.yandex.ru" xmlns:media="http://search.yahoo.com/mrss/" version="2.0">
<channel>
<title>{channel_title_esc}</title>
<link>{link_esc}</link>
<description>RSS feed for Dzen</description>
<language>ru</language>
{items_str}
</channel>
</rss>"""


@router.get("/rss/{user_id}", response_class=Response)
async def get_dzen_rss(
    user_id: int,
    token: Optional[str] = Query(None),
):
    """Отдаёт RSS 2.0 ленту постов Дзен для пользователя (для робота Дзена).
    Опционально: ?token=... сверяется с rss_token в профиле.
    """
    profile = await profile_service.get_dzen_profile(user_id)
    if profile and profile.get("rss_token") and profile.get("rss_token") != token:
        raise HTTPException(status_code=403, detail="Invalid or missing RSS token")
    channel_title = (profile or {}).get("channel_name") or f"Dzen {user_id}"
    base_url = (getattr(settings, "RSS_BASE_URL", None) or "").rstrip("/") or "http://localhost:8002"

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, title, post_text, post_date, images, videos
                FROM dzen_posts
                WHERE user_id = %s AND status = 'ready'
                  AND (post_date IS NULL OR post_date >= %s)
                ORDER BY COALESCE(post_date, created_at) DESC
                LIMIT 500
                """,
                (user_id, datetime.now(timezone.utc) - timedelta(days=8)),
            )
            rows = await cur.fetchall()
            cols = ["id", "title", "post_text", "post_date", "images", "videos"]
            posts = [dict(zip(cols, row)) for row in rows]
    finally:
        await release_db_connection(conn)

    xml = await _build_dzen_rss_xml(user_id, channel_title, base_url, posts)
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")

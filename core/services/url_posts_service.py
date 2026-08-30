"""Сервис сохранения постов из url-bot в таблицу url_posts."""

import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from database import get_db_connection, release_db_connection
from services.quota_service import ensure_monthly_post_quota
from exceptions import QuotaExceededError
from shared import async_fs
from storage_client import get_storage

logger = logging.getLogger(__name__)

# Каталог / ключ для скриншотов url (совпадает с путём в images)
UPLOADS_URL_DIR = "uploads/url"
S3_KEY_PREFIX = "uploads/url"


async def _save_screenshot_from_base64(screenshot_base64: str, user_id: int) -> str | None:
    """Декодирует base64, сохраняет в S3 (или локально). Возвращает путь /uploads/url/..."""
    if not screenshot_base64:
        return None
    try:
        data = base64.b64decode(screenshot_base64, validate=True)
    except Exception as e:
        logger.warning("Invalid screenshot base64: %s", e)
        return None
    if not data:
        return None
    try:
        date_part = datetime.utcnow().strftime("%Y-%m-%d")
        name = f"{uuid.uuid4().hex}.jpg"
        rel_path = f"{S3_KEY_PREFIX}/{user_id}/{date_part}/{name}"
        storage = get_storage()
        if storage:
            await storage.put(rel_path, data, content_type="image/jpeg")
            return f"/{rel_path}"
        from pathlib import Path

        dir_path = Path(UPLOADS_URL_DIR) / str(user_id) / date_part
        await async_fs.makedirs(dir_path)
        await async_fs.write_bytes(dir_path / name, data)
        return f"/{rel_path}"
    except Exception as e:
        logger.warning("Screenshot save failed: %s", e)
        return None


async def save_url_post(item: dict[str, Any]) -> int | None:
    """
    Сохраняет один пост из url-bot в url_posts.

    Если передан screenshot_base64 — сохраняет файл в uploads/url/... (S3) и в images кладёт путь.
    Если передан screenshot_path — в images кладёт путь как есть (файл уже должен быть в общем хранилище).

    Returns:
        id вставленной записи или None при ошибке.
    """
    user_id = item.get("user_id")
    url = item.get("url") or ""
    raw_post_text = item.get("post_text") or ""
    to_tg = item.get("to_tg", False)
    to_tw = item.get("to_tw", False)
    to_wp = item.get("to_wp", False)
    to_vk = item.get("to_vk", False)
    target_channels = item.get("target_channels") or []
    target_groups = item.get("target_groups") or []
    if not isinstance(target_channels, list):
        target_channels = []
    if not isinstance(target_groups, list):
        target_groups = []
    # Если выбраны конкретные каналы — включаем соответствующие флаги
    if target_channels:
        to_tg = True
    if target_groups:
        to_vk = True

    images: list[str] = []
    if item.get("screenshot_base64"):
        path = await _save_screenshot_from_base64(item["screenshot_base64"], user_id)
        if path:
            images.append(path)
    elif item.get("screenshot_path"):
        images.append(item["screenshot_path"])

    conn = await get_db_connection()
    try:
        if user_id is not None:
            try:
                await ensure_monthly_post_quota(int(user_id), conn=conn)
            except (TypeError, ValueError):
                pass
        async with conn.cursor() as cur:
            # screenshot_only: payload → match by item id / URL → legacy global.
            screenshot_only = False
            if "screenshot_only" in item:
                screenshot_only = bool(item.get("screenshot_only"))
            else:
                try:
                    await cur.execute(
                        "SELECT urls, screenshot_only FROM curl_settings WHERE user_id = %s",
                        (user_id,),
                    )
                    row = await cur.fetchone()
                    if row:
                        urls_raw, global_flag = row[0], row[1]
                        if isinstance(urls_raw, str):
                            try:
                                urls_raw = json.loads(urls_raw) if urls_raw else []
                            except (json.JSONDecodeError, TypeError):
                                urls_raw = []
                        matched = None
                        item_id = str(item.get("url_item_id") or item.get("id") or "").strip()
                        needle = (url or "").strip()
                        if isinstance(urls_raw, list):
                            if item_id:
                                for u in urls_raw:
                                    if not isinstance(u, dict):
                                        continue
                                    if str(u.get("id") or "").strip() == item_id:
                                        matched = u
                                        break
                            if matched is None and needle:
                                for u in urls_raw:
                                    if not isinstance(u, dict):
                                        continue
                                    if str(u.get("url") or "").strip() == needle:
                                        matched = u
                                        break
                                if matched is None:
                                    needle_norm = needle.rstrip("/")
                                    for u in urls_raw:
                                        if not isinstance(u, dict):
                                            continue
                                        if str(u.get("url") or "").strip().rstrip("/") == needle_norm:
                                            matched = u
                                            break
                        if matched is not None and "screenshot_only" in matched:
                            screenshot_only = bool(matched.get("screenshot_only"))
                        else:
                            screenshot_only = bool(global_flag)
                except Exception as e:
                    logger.warning("Failed to load screenshot_only for user %s: %s", user_id, e)

            post_date = datetime.utcnow()
            status = "collected"
            post_text = "" if screenshot_only else raw_post_text
            images_json = json.dumps(images, ensure_ascii=False)

            await cur.execute(
                """
                INSERT INTO url_posts (
                    user_id, url, post_text, post_date, images, status,
                    to_tg, to_tw, to_wp, to_vk, target_channels, target_groups
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id
                """,
                (
                    user_id,
                    url,
                    post_text,
                    post_date,
                    images_json,
                    status,
                    to_tg,
                    to_tw,
                    to_wp,
                    to_vk,
                    json.dumps(target_channels, ensure_ascii=False),
                    json.dumps(target_groups, ensure_ascii=False),
                ),
            )
            row = await cur.fetchone()
            url_post_id = row[0] if row else None
            return url_post_id
    except QuotaExceededError:
        raise
    except Exception as e:
        logger.exception("Save url post failed: %s", e)
        return None
    finally:
        await release_db_connection(conn)


async def save_url_posts_batch(items: list[dict[str, Any]]) -> list[int]:
    """Сохраняет несколько постов из url-bot. Возвращает список id вставленных записей."""
    ids: list[int] = []
    for item in items:
        post_id = await save_url_post(item)
        if post_id is not None:
            ids.append(post_id)
    return ids

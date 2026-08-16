"""Публикация постов со статусом ready в channel(s)_to_post."""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import httpx
from database import get_db_connection, release_db_connection
from config import settings
from storage_helper import get_storage
from shared.circuit_breaker import get_breaker
from shared.retry import retry_async
from shared import async_fs
from .client_manager import TelegramClientManager
from telethon.errors import FloodWaitError, RPCError


logger = logging.getLogger(__name__)

TG_MESSAGE_LIMIT = 4096


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _parse_json_list(raw: Any) -> List[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _now_in_time_windows(time_intervals: List[Dict], now: Optional[datetime] = None) -> bool:
    """True если сейчас попадаем в одно из окон HH:MM (start) ±15 мин или [start, end]."""
    if not time_intervals:
        return True
    now = now or datetime.now(timezone.utc).astimezone()
    current_minutes = now.hour * 60 + now.minute
    for interval in time_intervals:
        if not isinstance(interval, dict):
            continue
        start_s = str(interval.get("start") or "").strip()
        end_s = str(interval.get("end") or "").strip()
        if not start_s:
            continue
        try:
            sh, sm = [int(x) for x in start_s.split(":")[:2]]
            start_m = sh * 60 + sm
        except (ValueError, TypeError):
            continue
        if end_s:
            try:
                eh, em = [int(x) for x in end_s.split(":")[:2]]
                end_m = eh * 60 + em
            except (ValueError, TypeError):
                end_m = start_m + 15
            if start_m <= end_m:
                if start_m <= current_minutes <= end_m:
                    return True
            else:
                # через полночь
                if current_minutes >= start_m or current_minutes <= end_m:
                    return True
        else:
            # точка: окно ±15 минут
            if abs(current_minutes - start_m) <= 15 or abs(current_minutes - start_m) >= (24 * 60 - 15):
                return True
    return False


def _is_retryable_telegram_error(exc: BaseException) -> bool:
    """Transient TG errors — retry; FloodWait / auth — нет."""
    if isinstance(exc, FloodWaitError):
        return False
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if isinstance(exc, RPCError):
        msg = str(exc).lower()
        if any(
            x in msg
            for x in (
                "timeout",
                "timed out",
                "connection",
                "network",
                "unavailable",
                "datacenter",
                "server error",
                "internal",
            )
        ):
            return True
        return False
    msg = str(exc).lower()
    return any(x in msg for x in ("connection", "timeout", "timed out", "network", "503", "502"))


class PostPublisher:
    """Сервис публикации постов из tg_posts в Telegram канал(ы)."""

    def __init__(self, client_manager: TelegramClientManager):
        self.client_manager = client_manager

    async def get_ready_posts(self) -> List[Dict]:
        """Claim ready posts (SKIP LOCKED → publishing), then apply Python filters."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                claimed: List[Dict] = []
                try:
                    await cur.execute("BEGIN")
                    await cur.execute(
                        """
                        SELECT p.id, p.user_id, p.post_text, p.images, p.status,
                               p.publish_at, p.target_channels, p.url, p.title,
                               pr.channel_to_post, pr.channels_to_post,
                               pr.schedule_type, pr.time_intervals, pr.publish_enabled
                        FROM tg_posts p
                        JOIN tg_profiles pr ON p.user_id = pr.user_id
                        WHERE p.status = 'ready'
                          AND (p.publish_at IS NULL OR p.publish_at <= CURRENT_TIMESTAMP)
                        ORDER BY COALESCE(p.publish_at, p.created_at) ASC
                        LIMIT 50
                        FOR UPDATE OF p SKIP LOCKED
                        """
                    )
                    rows = await cur.fetchall()
                    columns = [col.name for col in cur.description]
                    if not rows:
                        await cur.execute("COMMIT")
                    else:
                        claimed = [dict(zip(columns, row)) for row in rows]
                        post_ids = [p["id"] for p in claimed]
                        ids_ph = ", ".join(["%s"] * len(post_ids))
                        await cur.execute(
                            f"""
                            UPDATE tg_posts
                            SET status = 'publishing', updated_at = CURRENT_TIMESTAMP
                            WHERE id IN ({ids_ph})
                            """,
                            post_ids,
                        )
                        await cur.execute("COMMIT")
                except Exception:
                    await cur.execute("ROLLBACK")
                    raise

                result: List[Dict] = []
                release_ids: List[int] = []
                for post in claimed:
                    if post.get("publish_enabled") is False:
                        release_ids.append(post["id"])
                        continue
                    schedule_type = (post.get("schedule_type") or "immediate").strip()
                    if schedule_type == "by_intervals":
                        intervals = _parse_json_list(post.get("time_intervals"))
                        if not _now_in_time_windows(intervals):
                            release_ids.append(post["id"])
                            continue
                    channels = self._resolve_channels(post)
                    if not channels:
                        release_ids.append(post["id"])
                        continue
                    post["_channels"] = channels
                    post["status"] = "publishing"
                    result.append(post)

                if release_ids:
                    ids_ph = ", ".join(["%s"] * len(release_ids))
                    await cur.execute(
                        f"""
                        UPDATE tg_posts
                        SET status = 'ready', updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({ids_ph})
                        """,
                        release_ids,
                    )

                if len(result) == 0:
                    await cur.execute(
                        "SELECT COUNT(*) FROM tg_posts WHERE status = 'ready'"
                    )
                    (ready_count,) = (await cur.fetchone()) or (0,)
                    await cur.execute(
                        """
                        SELECT COUNT(*) FROM tg_profiles
                        WHERE (
                            (channel_to_post IS NOT NULL AND channel_to_post != '')
                            OR (channels_to_post IS NOT NULL AND channels_to_post::text NOT IN ('[]', 'null'))
                        )
                        """
                    )
                    (profiles_with_channel,) = (await cur.fetchone()) or (0,)
                    logger.info(
                        "get_ready_posts returned 0 posts; "
                        "tg_posts with status=ready: %s, "
                        "tg_profiles with channel(s) set: %s",
                        ready_count,
                        profiles_with_channel,
                    )
                return result
        finally:
            await release_db_connection(conn)

    def _resolve_channels(self, post: Dict) -> List[str]:
        """Приоритет: target_channels поста → channels_to_post профиля → channel_to_post."""
        from .message_handler import MessageHandler

        def _ids(items: List[Any]) -> List[str]:
            result: List[str] = []
            for item in items:
                chat_id = MessageHandler.chat_ref_id(item)
                if chat_id:
                    result.append(chat_id)
            return result

        targets = _ids(_parse_json_list(post.get("target_channels")))
        if targets:
            return targets
        profile_channels = _ids(_parse_json_list(post.get("channels_to_post")))
        if profile_channels:
            return profile_channels
        single = MessageHandler.chat_ref_id(post.get("channel_to_post"))
        if single:
            return [single]
        return []

    def _resolve_image_path(self, image_path: str) -> Optional[str]:
        """Преобразует относительный путь изображения в абсолютный (только локальные пути)."""
        if not image_path or not isinstance(image_path, str):
            return None
        image_path = image_path.strip()
        if not image_path:
            return None
        if os.path.isabs(image_path) and os.path.exists(image_path):
            return os.path.abspath(image_path)
        path = image_path.lstrip("/")
        base = (settings.PATH_TO_TG_IMAGE or os.getcwd()).rstrip("/")
        full_path = os.path.join(base, path) if path else os.path.join(base, image_path)
        if os.path.exists(full_path):
            return os.path.abspath(full_path)
        if os.path.exists(image_path):
            return os.path.abspath(image_path)
        logger.debug(
            "Image file not found: tried %s and %s (base=%s)",
            full_path,
            image_path,
            base,
        )
        return None

    def _get_image_refs(self, images_raw) -> List[str]:
        """Извлекает пути/URL изображений из images (JSONB / list / dict)."""
        refs: List[str] = []
        if images_raw is None:
            return refs
        try:
            images = json.loads(images_raw) if isinstance(images_raw, str) else images_raw
            if not isinstance(images, list):
                return refs
            for item in images:
                if isinstance(item, str) and item.strip():
                    refs.append(item.strip())
                elif isinstance(item, dict):
                    ref = item.get("path") or item.get("url")
                    if ref and str(ref).strip():
                        refs.append(str(ref).strip())
        except (json.JSONDecodeError, TypeError):
            logger.debug("Failed to parse images for post: %s", type(images_raw))
        return refs

    def _get_first_image_ref(self, images_raw) -> Optional[str]:
        refs = self._get_image_refs(images_raw)
        return refs[0] if refs else None

    async def _download_image_url(self, url: str) -> Optional[str]:
        """Скачивает изображение по URL во временный файл."""
        if not url or not url.strip().lower().startswith(("http://", "https://")):
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                suffix = ".jpg"
                if "content-type" in resp.headers:
                    ct = (resp.headers.get("content-type") or "").lower()
                    if "png" in ct:
                        suffix = ".png"
                    elif "gif" in ct:
                        suffix = ".gif"
                    elif "webp" in ct:
                        suffix = ".webp"
                path = await async_fs.write_temp_bytes(resp.content, suffix=suffix)
                return path
        except Exception as e:
            logger.warning("Failed to download image from URL %s: %s", url[:80], e)
        return None

    async def resolve_image_for_publish(self, post_id: int, images_raw) -> Optional[str]:
        paths = await self.resolve_images_for_publish(post_id, images_raw)
        return paths[0] if paths else None

    async def resolve_images_for_publish(self, post_id: int, images_raw) -> List[str]:
        """Возвращает локальные пути к файлам изображений (альбом)."""
        refs = self._get_image_refs(images_raw)
        if not refs:
            logger.info(
                "Post id=%s: no image attached (images=%s)",
                post_id,
                str(images_raw)[:200] if images_raw is not None else "null",
            )
            return []
        result: List[str] = []
        storage = get_storage()
        for ref in refs:
            s = ref.strip()
            local_path: Optional[str] = None
            if s.lower().startswith(("http://", "https://")):
                local_path = await self._download_image_url(ref)
            else:
                if storage:
                    key = s.lstrip("/")
                    candidates = [key]
                    # bucket=uploads + path /uploads/url/... → также пробуем url/...
                    if key.startswith("uploads/"):
                        candidates.append(key[len("uploads/") :])
                    for candidate in candidates:
                        if not candidate:
                            continue
                        try:
                            body = await storage.get_bytes(candidate)
                        except Exception as exc:
                            logger.debug(
                                "Post id=%s: S3 get_bytes failed key=%s: %s",
                                post_id,
                                candidate,
                                exc,
                            )
                            body = None
                        if body:
                            suffix = ".jpg"
                            lower = candidate.lower()
                            if lower.endswith(".png"):
                                suffix = ".png"
                            elif lower.endswith(".webp"):
                                suffix = ".webp"
                            elif lower.endswith(".gif"):
                                suffix = ".gif"
                            local_path = await async_fs.write_temp_bytes(body, suffix=suffix)
                            break
                if not local_path:
                    local_path = self._resolve_image_path(ref)
            if local_path:
                result.append(local_path)
            else:
                logger.warning(
                    "Post id=%s: image file not found for ref=%s",
                    post_id,
                    ref[:120],
                )
        return result

    def _parse_channel_to_post(self, channel: str):
        """Преобразует channel_to_post в формат для send_message."""
        if not channel:
            return None
        channel = str(channel).strip()
        if channel.startswith("@"):
            return channel
        try:
            return int(channel)
        except ValueError:
            return channel

    async def _cleanup_temp(self, paths: List[str]) -> None:
        tmp = tempfile.gettempdir()
        for path in paths:
            if path and path.startswith(tmp):
                await async_fs.unlink_quiet(path)

    def _fallback_publish_text(self, post: Dict) -> str:
        """Текст для публикации при screenshot_only / пустом post_text."""
        text = (post.get("post_text") or "").strip()
        if text:
            return text
        title = (post.get("title") or "").strip()
        url = (post.get("url") or "").strip()
        if title and url:
            return f"{title}\n{url}"
        return title or url

    async def publish_post(self, post: Dict) -> bool:
        """Публикует один пост во все целевые каналы."""
        post_id = post.get("id")
        user_id = post.get("user_id")
        text = self._fallback_publish_text(post)
        channels = post.get("_channels") or self._resolve_channels(post)

        if not channels:
            logger.warning(f"Post {post_id}: no target channels for user {user_id}")
            return False

        breaker = get_breaker("telegram")
        if not breaker.allow_request():
            logger.warning("Post %s skipped: Telegram circuit open", post_id)
            return False

        client = self.client_manager.get_client(user_id)
        if not client:
            logger.warning(f"Post {post_id}: no active client for user {user_id}")
            return False

        image_paths = await self.resolve_images_for_publish(post_id, post.get("images"))

        if not text and not image_paths:
            logger.error(
                "Post %s: empty text and no images — marking as error (content issue, not Telegram)",
                post_id,
            )
            await self._update_post_status(post_id, "error")
            return False

        try:
            if len(text) >= TG_MESSAGE_LIMIT:
                text = text[: TG_MESSAGE_LIMIT - 3] + "..."
                image_paths = []

            async def _send_all() -> tuple[Any, Optional[str], list[str]]:
                last_message = None
                published_channels: list[str] = []
                for channel_raw in channels:
                    channel = self._parse_channel_to_post(channel_raw)
                    if not channel:
                        continue
                    if len(image_paths) > 1:
                        last_message = await client.send_file(
                            channel,
                            image_paths,
                            caption=text or None,
                        )
                    elif len(image_paths) == 1:
                        last_message = await client.send_file(
                            channel,
                            image_paths[0],
                            caption=text or None,
                            force_document=False,
                        )
                    else:
                        last_message = await client.send_message(channel, text)
                    published_channels.append(str(channel_raw))
                    _log_action(
                        "Published post %s to %s for user %s", post_id, channel, user_id
                    )
                chat_ids_joined = ",".join(published_channels) if published_channels else None
                return last_message, chat_ids_joined, published_channels

            last_message, chat_ids_joined, published_channels = await retry_async(
                _send_all,
                retry_on=_is_retryable_telegram_error,
                operation_name=f"publish_post id={post_id}",
            )

            if not published_channels:
                logger.error("Post %s: no channels published", post_id)
                return False

            message_id = getattr(last_message, "id", None) if last_message else None
            await self._update_post_published(post_id, message_id, chat_ids_joined)
            breaker.record_success()
            return True

        except FloodWaitError as e:
            logger.warning(
                "FloodWait publishing post %s: wait %ss (circuit not opened)",
                post_id,
                getattr(e, "seconds", "?"),
            )
            return False
        except ValueError as e:
            # Контент (пустое сообщение и т.п.) — не открываем circuit breaker
            logger.error("Post %s content error: %s — marking as error", post_id, e)
            await self._update_post_status(post_id, "error")
            return False
        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}", exc_info=True)
            breaker.record_failure()
            return False
        finally:
            await self._cleanup_temp(image_paths)

    async def _update_post_status(self, post_id: int, status: str) -> None:
        """Обновляет статус поста в tg_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tg_posts
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def _update_post_published(
        self,
        post_id: int,
        telegram_message_id: Optional[int],
        telegram_chat_id: Optional[str],
    ) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tg_posts
                    SET status = 'published',
                        telegram_message_id = COALESCE(%s, telegram_message_id),
                        telegram_chat_id = COALESCE(%s, telegram_chat_id),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (telegram_message_id, telegram_chat_id, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def edit_published_post(self, user_id: int, post_id: int, text: str) -> Dict:
        """Редактирует уже опубликованный пост в Telegram."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, post_text, telegram_message_id, telegram_chat_id, status
                    FROM tg_posts WHERE id = %s AND user_id = %s
                    """,
                    (post_id, user_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)

        if not row:
            return {"success": False, "error": "Post not found"}
        _id, _old_text, msg_id, chat_id, status = row
        if status != "published" or not msg_id or not chat_id:
            return {"success": False, "error": "Post is not published in Telegram"}

        client = self.client_manager.get_client(user_id)
        if not client:
            return {"success": False, "error": "No active Telegram client"}

        channel = self._parse_channel_to_post(str(chat_id))
        try:
            await client.edit_message(channel, int(msg_id), text[:TG_MESSAGE_LIMIT])
            await self._update_post_fields(post_id, post_text=text)
            return {"success": True}
        except Exception as e:
            logger.error("edit_published_post %s failed: %s", post_id, e, exc_info=True)
            return {"success": False, "error": str(e)}

    async def delete_published_post(self, user_id: int, post_id: int) -> Dict:
        """Удаляет опубликованный пост из Telegram и помечает deleted в БД."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT telegram_message_id, telegram_chat_id, status
                    FROM tg_posts WHERE id = %s AND user_id = %s
                    """,
                    (post_id, user_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)

        if not row:
            return {"success": False, "error": "Post not found"}
        msg_id, chat_id, status = row
        client = self.client_manager.get_client(user_id)
        if status == "published" and msg_id and chat_id and client:
            try:
                channel = self._parse_channel_to_post(str(chat_id))
                await client.delete_messages(channel, [int(msg_id)])
            except Exception as e:
                logger.warning("Failed to delete TG message for post %s: %s", post_id, e)

        await self._update_post_status(post_id, "deleted")
        return {"success": True}

    async def _update_post_fields(self, post_id: int, **fields) -> None:
        if not fields:
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                sets = ", ".join(f"{k} = %s" for k in fields)
                values = list(fields.values()) + [post_id]
                await cur.execute(
                    f"""
                    UPDATE tg_posts SET {sets}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    values,
                )
        finally:
            await release_db_connection(conn)

    async def get_upcoming_schedule(self, hours: int = 24, user_id: Optional[int] = None) -> List[Dict]:
        """Очередь постов на ближайшие N часов (publish_at в будущем или ready без даты)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: List[Any] = [hours]
                user_filter = ""
                if user_id is not None:
                    user_filter = "AND p.user_id = %s"
                    params.append(user_id)
                await cur.execute(
                    f"""
                    SELECT p.id, p.user_id, p.post_text, p.status, p.publish_at,
                           p.created_at, p.target_channels, pr.channel_to_post, pr.channels_to_post
                    FROM tg_posts p
                    JOIN tg_profiles pr ON p.user_id = pr.user_id
                    WHERE p.status IN ('ready', 'collected', 'review')
                      AND (
                        (p.publish_at IS NOT NULL AND p.publish_at <= CURRENT_TIMESTAMP + (%s || ' hours')::interval)
                        OR (p.publish_at IS NULL AND p.status = 'ready')
                      )
                      {user_filter}
                    ORDER BY COALESCE(p.publish_at, p.created_at) ASC
                    LIMIT 200
                    """,
                    params,
                )
                rows = await cur.fetchall()
                columns = [col.name for col in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        finally:
            await release_db_connection(conn)

    async def publish_ready_posts(self) -> int:
        """Публикует все посты со статусом ready, у которых наступило publish_at."""
        posts = await self.get_ready_posts()
        _log_action("get_ready_posts returned %d posts", len(posts))
        if not posts:
            return 0

        published = 0
        for post in posts:
            if await self.publish_post(post):
                published += 1
            await asyncio.sleep(20)

        _log_action("publish_ready_posts: published %d of %d", published, len(posts))
        return published

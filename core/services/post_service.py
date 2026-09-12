"""Сервис для управления постами."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import get_db_connection, release_db_connection
from services.quota_service import ensure_monthly_post_quota
from services.unified_post_ops import (
    create_unified_post,
    get_platform_post,
    list_platform_posts,
    update_platform_post,
)


from shared.db.posts_repo import (
    LEGACY_FLAG_TO_PLATFORM,
    PostsRepository,
    flags_from_platforms,
    resolve_publish_platforms,
)
from shared.post_adapt import NETWORK_TEXT_LIMITS as _SHARED_NETWORK_TEXT_LIMITS
from shared.queue_wakeup import wake_process_http


async def _wake_collector_for_status(status: str) -> None:
    if status not in ("collected", "created"):
        return
    try:
        from config import settings

        await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
    except Exception:
        pass


async def _attach_destination_flags(cur, posts: List[Dict]) -> None:
    for post in posts:
        for flag_name in LEGACY_FLAG_TO_PLATFORM:
            post[flag_name] = False
    ids = [int(post["id"]) for post in posts if post.get("id") is not None]
    if not ids:
        return
    await cur.execute(
        """
        SELECT post_id, platform
        FROM post_targets
        WHERE post_id = ANY(%s)
          AND status NOT IN ('deleted', 'skipped')
        """,
        (ids,),
    )
    by_id: Dict[int, List[str]] = {}
    for post_id, platform in await cur.fetchall():
        by_id.setdefault(int(post_id), []).append(str(platform))
    for post in posts:
        post.update(flags_from_platforms(by_id.get(int(post["id"]), [])))


async def _sync_destination_flags(
    cur,
    *,
    user_id: int,
    post_id: int,
    hub_status: str,
    dest: Dict[str, Optional[bool]],
) -> None:
    enabled = [platform for platform, value in dest.items() if value is True]
    disabled = [platform for platform, value in dest.items() if value is False]
    if enabled:
        target_status = "ready" if hub_status == "ready" else "pending"
        await PostsRepository(cur).ensure_targets(
            post_id=post_id,
            user_id=user_id,
            platforms=enabled,
            status=target_status,
        )
    if disabled:
        await cur.execute(
            """
            UPDATE post_targets
            SET status = 'skipped', updated_at = CURRENT_TIMESTAMP
            WHERE post_id = %s
              AND platform = ANY(%s)
              AND status IN ('pending', 'ready')
            """,
            (post_id, disabled),
        )


class PostService:
    """Сервис для создания и управления постами."""

    # Re-export shared limits; cpost uses wp ceiling for manual multi-target
    PLATFORM_LIMITS = {
        **_SHARED_NETWORK_TEXT_LIMITS,
        "cpost": _SHARED_NETWORK_TEXT_LIMITS["wp"],
    }

    async def _unified_list(
        self,
        platform: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Dict]:
        rows = await list_platform_posts(
            user_id=user_id,
            platform=platform,
            limit=limit,
            offset=offset,
            **kwargs,
        )
        return [self._row_to_post(row) for row in rows]

    async def _unified_get(self, platform: str, user_id: int, post_id: int) -> Optional[Dict]:
        row = await get_platform_post(user_id=user_id, post_id=post_id, platform=platform)
        return self._row_to_post(row) if row else None

    async def _unified_update(self, platform: str, user_id: int, post_id: int, **kwargs: Any) -> Optional[Dict]:
        row = await update_platform_post(
            user_id=user_id,
            post_id=post_id,
            platform=platform,
            **kwargs,
        )
        return self._row_to_post(row) if row else None
    
    async def create_post(
        self,
        user_id: int,
        text: str,
        platform: str,
        title: Optional[str] = None,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        **kwargs
    ) -> Dict:
        """Создает новый пост.
        
        Args:
            user_id: ID пользователя
            text: Текст поста
            platform: Исходная платформа (tg, tw, wp, vk, cpost)
            title: Заголовок поста (опционально)
            to_tg: Отправлять в Telegram
            to_tw: Отправлять в Twitter
            to_wp: Отправлять в WordPress
            to_vk: Отправлять в VKontakte
            **kwargs: Дополнительные поля поста
            
        Returns:
            Созданный пост
            
        Raises:
            ValueError: Если текст превышает лимит платформы
        """
        # Проверка лимита символов
        limit = self.PLATFORM_LIMITS.get(platform, 150000)
        if len(text) > limit:
            raise ValueError(f"Text exceeds {platform} limit of {limit} characters")

        conn = await get_db_connection()
        try:
            await ensure_monthly_post_quota(user_id, conn=conn)
            hub_status = str(kwargs.get("status", "collected"))
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, source_platform
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        title,
                        kwargs.get("domain"),
                        kwargs.get("url"),
                        kwargs.get("author"),
                        kwargs.get("avatar"),
                        kwargs.get("post_date"),
                        kwargs.get("screenshot"),
                        json.dumps(kwargs.get("images", [])),
                        kwargs.get("image_over_text"),
                        kwargs.get("comments", 0),
                        kwargs.get("reposts", 0),
                        kwargs.get("likes", 0),
                        kwargs.get("views", 0),
                        kwargs.get("is_ad", False),
                        hub_status,
                        platform,
                        platform,
                    )
                )
                row = await cur.fetchone()
                post = self._row_to_post(row, cur.description)
                platforms = resolve_publish_platforms(
                    legacy_flags={
                        "to_tg": to_tg,
                        "to_tw": to_tw,
                        "to_wp": to_wp,
                        "to_vk": to_vk,
                        "to_threads": to_threads,
                        "to_dzen": to_dzen,
                        "to_instagram": to_instagram,
                    },
                    source_platform=platform,
                )
                if platforms:
                    target_status = "ready" if hub_status == "ready" else "pending"
                    await PostsRepository(cur).ensure_targets(
                        post_id=int(post["id"]),
                        user_id=user_id,
                        platforms=platforms,
                        status=target_status,
                    )
                post.update(flags_from_platforms(platforms))
                await _wake_collector_for_status(hub_status)
                return post
        finally:
            await release_db_connection(conn)

    async def create_wp_post_record(
        self,
        user_id: int,
        text: str,
        title: Optional[str] = None,
        *,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = True,
        to_vk: bool = False,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
        status: str = "ready",
        skip_quota: bool = False,
    ) -> Dict:
        """Создает пост WordPress в ``posts`` + ``post_targets``.

        Outbound publish uses status=ready (default). Collected/inbound posts
        are inserted by wp-bot collect with status=collected.
        """
        limit = self.PLATFORM_LIMITS.get("wp", 150000)
        if len(text) > limit:
            raise ValueError(f"Text exceeds wp limit of {limit} characters")

        allowed_status = {"ready", "collected", "draft", "pending_approval"}
        post_status = status if status in allowed_status else "ready"
        hub_status = "ready" if post_status == "ready" else "collected"
        target_status = "ready" if hub_status == "ready" else "pending"
        row = await create_unified_post(
            user_id=user_id,
            source_platform="wp",
            text=text,
            title=title,
            status=hub_status,
            target_status=target_status,
            skip_quota=skip_quota,
            target_channels=target_channels,
            target_groups=target_groups,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            return_platform="wp",
        )
        return self._row_to_post(row)

    async def create_tg_post_record(
        self,
        user_id: int,
        text: str,
        images: Optional[List[str]] = None,
        *,
        to_tg: bool = True,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        publish_at: Optional[Any] = None,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        skip_quota: bool = False,
        status: str = "collected",
    ) -> Dict:
        """Создает пост Telegram в posts / post_targets."""
        # Проверка лимита символов для Telegram
        limit = self.PLATFORM_LIMITS.get("tg", 4096)
        if len(text) > limit:
            raise ValueError(f"Text exceeds tg limit of {limit} characters")

        row = await create_unified_post(
            user_id=user_id,
            source_platform="tg",
            text=text,
            images=images,
            brand_id=brand_id,
            channel_id=channel_id,
            target_channels=target_channels,
            target_groups=target_groups,
            publish_at=publish_at,
            status=status,
            skip_quota=skip_quota,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            return_platform="tg",
        )
        return self._row_to_post(row)

    async def create_cpost_post_record(
        self,
        user_id: int,
        text: str,
        title: Optional[str] = None,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        status: str = "collected",
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict:
        """Создаёт ручной пост в cpost_posts (далее collector переносит в posts)."""
        limit = self.PLATFORM_LIMITS.get("cpost", 150000)
        if len(text) > limit:
            raise ValueError(f"Text exceeds cpost limit of {limit} characters")

        extras = {
            "metadata": {
                "image_over_text": kwargs.get("image_over_text"),
                "comments": kwargs.get("comments", 0),
                "reposts": kwargs.get("reposts", 0),
                "likes": kwargs.get("likes", 0),
                "views": kwargs.get("views", 0),
                "is_ad": kwargs.get("is_ad", False),
            }
        }
        hub_status = status if status in ("collected", "created", "ready", "review") else "collected"
        row = await create_unified_post(
            user_id=user_id,
            source_platform="cpost",
            text=text,
            title=title,
            url=kwargs.get("url"),
            images=kwargs.get("images") or [],
            extras=extras,
            target_channels=target_channels,
            target_groups=target_groups,
            status=hub_status,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            return_platform="cpost",
        )
        return self._row_to_post(row)

    async def create_tw_post_record(
        self,
        user_id: int,
        text: str,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
    ) -> Dict:
        """Создаёт пост Twitter в tw_posts (далее collector переносит в posts)."""
        limit = self.PLATFORM_LIMITS.get("tw", 280)
        if len(text) > limit:
            raise ValueError(f"Text exceeds tw limit of {limit} characters")

        row = await create_unified_post(
            user_id=user_id,
            source_platform="tw",
            text=text,
            target_channels=target_channels,
            target_groups=target_groups,
            status="collected",
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            return_platform="tw",
        )
        return self._row_to_post(row)

    async def get_tw_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Посты пользователя из tw_posts (очередь / история)."""
        rows = await list_platform_posts(user_id=user_id, platform="tw", limit=limit, offset=offset)
        return [self._row_to_post(row) for row in rows]

    async def get_cpost_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Список ручных постов из cpost_posts."""
        return await self._unified_list("cpost", user_id, limit, offset)

    async def get_cpost_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Один ручной пост по id в cpost_posts."""
        return await self._unified_get("cpost", user_id, post_id)

    async def update_cpost_post(
        self,
        user_id: int,
        post_id: int,
        title: Optional[str] = None,
        post_text: Optional[str] = None,
        images: Optional[list] = None,
        status: Optional[str] = None,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[Dict]:
        return await self._unified_update(
            'cpost',
            user_id,
            post_id,
            title=title,
            post_text=post_text,
            images=images,
            status=status,
            target_channels=target_channels,
            target_groups=target_groups,
        )

    async def delete_cpost_post(self, user_id: int, post_id: int) -> bool:
        row = await self._unified_update('cpost', user_id, post_id, status='deleted')
        return row is not None

    async def get_posts(
        self,
        user_id: int,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        post_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Получает посты пользователя.
        
        Args:
            user_id: ID пользователя
            status: Фильтр по статусу
            platform: Фильтр по цели в post_targets (tg, tw, ...)
            post_type: Фильтр по типу поста (например 'cpost')
            limit: Лимит записей
            offset: Смещение
            
        Returns:
            Список постов
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                query = "SELECT * FROM posts WHERE user_id = %s"
                params = [user_id]
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                if post_type is not None:
                    query += " AND post_type = %s"
                    params.append(post_type)
                
                if platform:
                    query += """
                        AND EXISTS (
                            SELECT 1 FROM post_targets t
                            WHERE t.post_id = posts.id
                              AND t.platform = %s
                              AND t.status NOT IN ('deleted', 'skipped')
                        )
                    """
                    params.append(platform)

                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                await cur.execute(query, params)
                rows = await cur.fetchall()
                posts = [self._row_to_post(row, cur.description) for row in rows]
                await _attach_destination_flags(cur, posts)
                return posts
        finally:
            await release_db_connection(conn)

    async def get_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост из таблицы posts по id.
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            Пост или None
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                row = await cur.fetchone()
                if row:
                    post = self._row_to_post(row, cur.description)
                    await _attach_destination_flags(cur, [post])
                    return post
                return None
        finally:
            await release_db_connection(conn)

    async def get_all_posts(
        self,
        limit: int = 500,
        offset: int = 0,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[Dict]:
        """Получает посты из таблицы posts (для админки). Опционально по status и user_id (только посты автора)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                conditions = []
                params: list = []
                if user_id is not None:
                    conditions.append("p.user_id = %s")
                    params.append(user_id)
                if status:
                    conditions.append("p.status = %s")
                    params.append(status)
                where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
                params.extend([limit, offset])
                await cur.execute(
                    f"""
                    SELECT p.*,
                           CASE
                             WHEN t_tg.result ? 'telegram_chat_id' THEN t_tg.result->>'telegram_chat_id'
                             ELSE NULL
                           END AS published_channel,
                           CASE WHEN t_tg.id IS NOT NULL THEN 'tg' ELSE NULL END AS target_hint_tg,
                           CASE WHEN t_tw.id IS NOT NULL THEN 'tw' ELSE NULL END AS target_hint_tw,
                           CASE WHEN t_wp.id IS NOT NULL THEN 'wp' ELSE NULL END AS target_hint_wp,
                           CASE WHEN t_vk.id IS NOT NULL THEN 'vk' ELSE NULL END AS target_hint_vk,
                           CASE WHEN t_th.id IS NOT NULL THEN 'threads' ELSE NULL END AS target_hint_threads,
                           CASE WHEN t_dz.id IS NOT NULL THEN 'dzen' ELSE NULL END AS target_hint_dzen,
                           CASE WHEN t_ig.id IS NOT NULL THEN 'instagram' ELSE NULL END AS target_hint_instagram
                    FROM posts p
                    LEFT JOIN post_targets t_tg ON t_tg.post_id = p.id AND t_tg.platform = 'tg'
                    LEFT JOIN post_targets t_tw ON t_tw.post_id = p.id AND t_tw.platform = 'tw'
                    LEFT JOIN post_targets t_wp ON t_wp.post_id = p.id AND t_wp.platform = 'wp'
                    LEFT JOIN post_targets t_vk ON t_vk.post_id = p.id AND t_vk.platform = 'vk'
                    LEFT JOIN post_targets t_th ON t_th.post_id = p.id AND t_th.platform = 'threads'
                    LEFT JOIN post_targets t_dz ON t_dz.post_id = p.id AND t_dz.platform = 'dzen'
                    LEFT JOIN post_targets t_ig ON t_ig.post_id = p.id AND t_ig.platform = 'instagram'
                    {where}
                    ORDER BY p.id DESC
                    LIMIT %s OFFSET %s
                    """,
                    params,
                )
                rows = await cur.fetchall()
                posts = []
                for row in rows:
                    post = self._row_to_post(row, cur.description)
                    channel = post.pop("published_channel", None)
                    hints = [
                        post.pop(k, None)
                        for k in (
                            "target_hint_tg",
                            "target_hint_tw",
                            "target_hint_wp",
                            "target_hint_vk",
                            "target_hint_threads",
                            "target_hint_dzen",
                            "target_hint_instagram",
                        )
                    ]
                    targets = [h for h in hints if h]
                    if isinstance(channel, str) and "," in channel:
                        channel = ", ".join(
                            part.strip() for part in channel.split(",") if part.strip()
                        )
                    if channel:
                        post["published_channel"] = str(channel)
                    elif targets:
                        post["published_channel"] = "→ " + ",".join(targets)
                    else:
                        post["published_channel"] = None
                    posts.append(post)
                await _attach_destination_flags(cur, posts)
                return posts
        finally:
            await release_db_connection(conn)

    async def update_post(
        self,
        user_id: int,
        post_id: int,
        title: Optional[str] = None,
        post_text: Optional[str] = None,
        domain: Optional[str] = None,
        url: Optional[str] = None,
        author: Optional[str] = None,
        avatar: Optional[str] = None,
        post_date: Optional[datetime] = None,
        screenshot: Optional[str] = None,
        images: Optional[list] = None,
        image_over_text: Optional[str] = None,
        comments: Optional[int] = None,
        reposts: Optional[int] = None,
        likes: Optional[int] = None,
        views: Optional[int] = None,
        is_ad: Optional[bool] = None,
        status: Optional[str] = None,
        to_tg: Optional[bool] = None,
        to_tw: Optional[bool] = None,
        to_wp: Optional[bool] = None,
        to_vk: Optional[bool] = None,
        to_threads: Optional[bool] = None,
        to_dzen: Optional[bool] = None,
        to_instagram: Optional[bool] = None,
    ) -> Optional[Dict]:
        """Обновляет пост в таблице posts (все переданные поля)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if title is not None:
                    updates.append("title = %s")
                    params.append(title)
                if post_text is not None:
                    updates.append("post_text = %s")
                    params.append(post_text)
                if domain is not None:
                    updates.append("domain = %s")
                    params.append(domain)
                if url is not None:
                    updates.append("url = %s")
                    params.append(url)
                if author is not None:
                    updates.append("author = %s")
                    params.append(author)
                if avatar is not None:
                    updates.append("avatar = %s")
                    params.append(avatar)
                if post_date is not None:
                    updates.append("post_date = %s")
                    params.append(post_date)
                if screenshot is not None:
                    updates.append("screenshot = %s")
                    params.append(screenshot)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if image_over_text is not None:
                    updates.append("image_over_text = %s")
                    params.append(image_over_text)
                if comments is not None:
                    updates.append("comments = %s")
                    params.append(comments)
                if reposts is not None:
                    updates.append("reposts = %s")
                    params.append(reposts)
                if likes is not None:
                    updates.append("likes = %s")
                    params.append(likes)
                if views is not None:
                    updates.append("views = %s")
                    params.append(views)
                if is_ad is not None:
                    updates.append("is_ad = %s")
                    params.append(is_ad)
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                dest = {
                    "tg": to_tg,
                    "tw": to_tw,
                    "wp": to_wp,
                    "vk": to_vk,
                    "threads": to_threads,
                    "dzen": to_dzen,
                    "instagram": to_instagram,
                }
                has_dest = any(value is not None for value in dest.values())
                if not updates and not has_dest:
                    return await self.get_post(user_id, post_id)
                if updates:
                    params.extend([user_id, post_id])
                    query = f"""
                        UPDATE posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND id = %s
                        RETURNING *
                    """
                    await cur.execute(query, params)
                    row = await cur.fetchone()
                else:
                    await cur.execute(
                        "SELECT * FROM posts WHERE user_id = %s AND id = %s",
                        (user_id, post_id),
                    )
                    row = await cur.fetchone()
                if not row:
                    return None
                post = self._row_to_post(row, cur.description)
                if has_dest:
                    await _sync_destination_flags(
                        cur,
                        user_id=user_id,
                        post_id=post_id,
                        hub_status=str(post.get("status") or ""),
                        dest=dest,
                    )
                await _attach_destination_flags(cur, [post])
                return post
        finally:
            await release_db_connection(conn)

    async def delete_post(self, user_id: int, post_id: int) -> bool:
        """Удаляет пост из таблицы posts.
        
        Args:
            user_id: ID пользователя
            post_id: ID поста
            
        Returns:
            True если пост удален, False если не найден
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def get_wp_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        return await self._unified_list("wp", user_id, limit, offset)

    async def get_wp_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("wp", user_id, post_id)

    async def update_wp_post(
        self,
        user_id: int,
        post_id: int,
        title: Optional[str] = None,
        post_text: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        return await self._unified_update(
            "wp", user_id, post_id, title=title, post_text=post_text, status=status
        )

    async def delete_wp_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост WordPress как удаленный (status = 'deleted').

        Args:
            user_id: ID пользователя
            post_id: ID поста

        Returns:
            Обновленный пост или None
        """
        return await self.update_wp_post(user_id, post_id, status="deleted")

    async def get_tg_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        return await self._unified_list(
            "tg",
            user_id,
            limit,
            offset,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_tg_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("tg", user_id, post_id)

    async def update_tg_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
        publish_at: Optional[Any] = None,
        clear_publish_at: bool = False,
        target_channels: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        if text is not None:
            limit = self.PLATFORM_LIMITS.get("tg", 4096)
            if len(text) > limit:
                raise ValueError(f"Text exceeds tg limit of {limit} characters")
        return await self._unified_update(
            "tg",
            user_id,
            post_id,
            post_text=text,
            images=images,
            status=status,
            publish_at=publish_at,
            clear_publish_at=clear_publish_at,
            target_channels=target_channels,
        )

    async def delete_tg_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Telegram как удаленный (status = 'deleted').

        Args:
            user_id: ID пользователя
            post_id: ID поста

        Returns:
            Обновленный пост или None
        """
        return await self.update_tg_post(user_id, post_id, status="deleted")

    async def approve_tg_post(
        self,
        user_id: int,
        post_id: int,
        publish_at: Optional[Any] = None,
    ) -> Optional[Dict]:
        """Approve review → ready (+ optional schedule)."""
        return await self.update_tg_post(
            user_id,
            post_id,
            status="ready",
            publish_at=publish_at,
        )

    # ==================== TG templates ====================

    async def list_tg_templates(self, user_id: int) -> List[Dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, name, text, hashtags, created_at, updated_at
                    FROM tg_post_templates
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def create_tg_template(
        self,
        user_id: int,
        name: str,
        text: str,
        hashtags: str = "",
    ) -> Dict:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tg_post_templates (user_id, name, text, hashtags)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id, name, text, hashtags, created_at, updated_at
                    """,
                    (user_id, name[:200], text, hashtags or ""),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def delete_tg_template(self, user_id: int, template_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM tg_post_templates
                    WHERE user_id = %s AND id = %s
                    """,
                    (user_id, template_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    # ==================== Threads ====================

    async def create_threads_post_record(
        self,
        user_id: int,
        text: str,
        images: Optional[List[str]] = None,
        *,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_threads: bool = True,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
    ) -> Dict:
        """Создает пост Threads в таблице threads_posts."""
        limit = self.PLATFORM_LIMITS.get("threads", 500)
        if len(text) > limit:
            raise ValueError(f"Text exceeds threads limit of {limit} characters")

        row = await create_unified_post(
            user_id=user_id,
            source_platform="threads",
            text=text,
            images=images,
            target_channels=target_channels,
            target_groups=target_groups,
            status="collected",
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            return_platform="threads",
        )
        return self._row_to_post(row)

    async def get_threads_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        return await self._unified_list("threads", user_id, limit, offset)

    async def get_threads_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("threads", user_id, post_id)

    async def update_threads_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        return await self._unified_update(
            "threads", user_id, post_id, post_text=text, images=images, status=status
        )

    async def delete_threads_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Threads как удаленный (status = 'deleted')."""
        return await self.update_threads_post(user_id, post_id, status="deleted")

    async def create_vk_post_record(
        self,
        user_id: int,
        text: str,
        images: Optional[List[str]] = None,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = True,
        to_threads: bool = False,
        to_dzen: bool = False,
        to_instagram: bool = False,
        publish_at: Optional[Any] = None,
        target_groups: Optional[List[str]] = None,
        target_channels: Optional[List[str]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        skip_quota: bool = False,
    ) -> Dict:
        """Создаёт пост VKontakte в таблице vk_posts (status=created; collector переносит в posts, затем pipeline до ready для публикации)."""
        limit = self.PLATFORM_LIMITS.get("vk", 15985)
        if len(text) > limit:
            raise ValueError(f"Text exceeds vk limit of {limit} characters")

        images = images or []
        attachments = [{"type": "photo", "path": p} for p in images] if images else []
        row = await create_unified_post(
            user_id=user_id,
            source_platform="vk",
            text=text,
            images=images,
            extras={"attachments": attachments},
            brand_id=brand_id,
            channel_id=channel_id,
            target_channels=target_channels,
            target_groups=target_groups,
            publish_at=publish_at,
            status="created",
            skip_quota=skip_quota,
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_threads=to_threads,
            to_dzen=to_dzen,
            to_instagram=to_instagram,
            return_platform="vk",
        )
        return self._row_to_post(row)

    async def get_vk_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        return await self._unified_list(
            "vk", user_id, limit, offset, date_from=date_from, date_to=date_to
        )

    async def get_vk_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("vk", user_id, post_id)

    async def update_vk_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attachments: Optional[List] = None,
        status: Optional[str] = None,
        publish_at: Optional[Any] = None,
        clear_publish_at: bool = False,
    ) -> Optional[Dict]:
        extras = {"attachments": attachments} if attachments is not None else None
        return await self._unified_update(
            "vk",
            user_id,
            post_id,
            post_text=text,
            images=images,
            extras=extras,
            status=status,
            publish_at=publish_at,
            clear_publish_at=clear_publish_at,
        )

    async def delete_vk_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост VKontakte как удаленный (status = 'deleted')."""
        return await self.update_vk_post(user_id, post_id, status="deleted")

    async def get_url_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        return await self._unified_list("url", user_id, limit, offset)

    async def update_post_status(self, post_id: int, status: str) -> Optional[Dict]:
        """Обновляет статус поста.
        
        Args:
            post_id: ID поста
            status: Новый статус (collected, processed, published)
            
        Returns:
            Обновленный пост или None
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE posts SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                    """,
                    (status, post_id)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)
    
    def _row_to_post(self, row, description=None) -> Dict:
        """Преобразует строку БД или dict репозитория в словарь поста."""
        if isinstance(row, dict):
            post = dict(row)
        else:
            columns = [col.name for col in description]
            post = dict(zip(columns, row))
        if isinstance(post.get("images"), str):
            try:
                post["images"] = json.loads(post["images"])
            except (json.JSONDecodeError, TypeError):
                post["images"] = []
        if isinstance(post.get("videos"), str):
            try:
                post["videos"] = json.loads(post["videos"])
            except (json.JSONDecodeError, TypeError):
                post["videos"] = []
        if isinstance(post.get("attachments"), str):
            try:
                post["attachments"] = json.loads(post["attachments"])
            except (json.JSONDecodeError, TypeError):
                post["attachments"] = []
        if isinstance(post.get("target_channels"), str):
            try:
                post["target_channels"] = json.loads(post["target_channels"])
            except (json.JSONDecodeError, TypeError):
                post["target_channels"] = []
        elif post.get("target_channels") is None:
            post["target_channels"] = []
        if isinstance(post.get("target_groups"), str):
            try:
                post["target_groups"] = json.loads(post["target_groups"])
            except (json.JSONDecodeError, TypeError):
                post["target_groups"] = []
        for dt_key in ("publish_at", "created_at", "updated_at", "post_date"):
            val = post.get(dt_key)
            if hasattr(val, "isoformat"):
                post[dt_key] = val.isoformat()
        return post

    # ==================== Dzen ====================

    async def create_dzen_post_record(
        self,
        user_id: int,
        text: str,
        title: Optional[str] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_dzen: bool = True,
        to_threads: bool = False,
        to_instagram: bool = False,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
    ) -> Dict:
        """Создает пост Дзен в таблице dzen_posts."""
        limit = self.PLATFORM_LIMITS.get("dzen", 1500)
        if len(text) > limit:
            raise ValueError(f"Text exceeds dzen limit of {limit} characters")

        row = await create_unified_post(
            user_id=user_id,
            source_platform="dzen",
            text=text,
            title=title,
            images=images,
            videos=videos,
            target_channels=target_channels,
            target_groups=target_groups,
            status="collected",
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_dzen=to_dzen,
            to_threads=to_threads,
            to_instagram=to_instagram,
            return_platform="dzen",
        )
        return self._row_to_post(row)

    async def get_dzen_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        return await self._unified_list("dzen", user_id, limit, offset)

    async def get_dzen_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("dzen", user_id, post_id)

    async def update_dzen_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        title: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        return await self._unified_update(
            "dzen",
            user_id,
            post_id,
            post_text=text,
            title=title,
            images=images,
            status=status,
        )

    async def delete_dzen_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Дзен как удаленный (status = 'deleted')."""
        return await self.update_dzen_post(user_id, post_id, status="deleted")

    # ==================== Instagram ====================

    async def create_instagram_post_record(
        self,
        user_id: int,
        caption: str,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        to_tg: bool = False,
        to_tw: bool = False,
        to_wp: bool = False,
        to_vk: bool = False,
        to_dzen: bool = False,
        to_threads: bool = False,
        to_instagram: bool = True,
        target_channels: Optional[List[str]] = None,
        target_groups: Optional[List[str]] = None,
    ) -> Dict:
        """Создает пост Instagram в таблице instagram_posts (status=ready для ручной публикации)."""
        limit = self.PLATFORM_LIMITS.get("instagram", 2200)
        if len(caption) > limit:
            raise ValueError(f"Caption exceeds instagram limit of {limit} characters")

        row = await create_unified_post(
            user_id=user_id,
            source_platform="instagram",
            text=caption,
            images=images,
            videos=videos,
            target_channels=target_channels,
            target_groups=target_groups,
            status="ready",
            to_tg=to_tg,
            to_tw=to_tw,
            to_wp=to_wp,
            to_vk=to_vk,
            to_dzen=to_dzen,
            to_threads=to_threads,
            to_instagram=to_instagram,
            return_platform="instagram",
        )
        return self._row_to_post(row)

    async def get_instagram_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        return await self._unified_list("instagram", user_id, limit, offset)

    async def get_instagram_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        return await self._unified_get("instagram", user_id, post_id)

    async def update_instagram_post(
        self,
        user_id: int,
        post_id: int,
        caption: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        if caption is not None:
            limit = self.PLATFORM_LIMITS.get("instagram", 2200)
            if len(caption) > limit:
                raise ValueError(f"Caption exceeds instagram limit of {limit} characters")
        return await self._unified_update(
            "instagram", user_id, post_id, post_text=caption, images=images, status=status
        )

    async def delete_instagram_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Instagram как удаленный (status = 'deleted')."""
        return await self.update_instagram_post(user_id, post_id, status="deleted")


post_service = PostService()

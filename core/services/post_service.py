"""Сервис для управления постами."""

import json
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db_connection, release_db_connection
from services.quota_service import ensure_monthly_post_quota


class PostService:
    """Сервис для создания и управления постами."""
    
    # Лимиты символов для разных платформ
    PLATFORM_LIMITS = {
        "tg": 4096,
        "tw": 280,
        "wp": 150000,
        "vk": 15985,
        "cpost": 150000,
        "threads": 500,
        "dzen": 1500,
        "instagram": 2200,
    }
    
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

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
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
                        kwargs.get("status", "collected"),
                        platform,
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                        to_dzen,
                        to_instagram,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
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
    ) -> Dict:
        """Создает пост WordPress в таблице wp_posts.
        
        Args:
            user_id: ID пользователя
            text: Текст поста (HTML, до 150000 символов)
            title: Заголовок поста
            to_*: цели дублирования
        
        Returns:
            Созданный пост из таблицы wp_posts
        """
        # Проверка лимита символов для WordPress
        limit = self.PLATFORM_LIMITS.get("wp", 150000)
        if len(text) > limit:
            raise ValueError(f"Text exceeds wp limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO wp_posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    ) VALUES (
                        %s, %s, %s, NULL, NULL, NULL, NULL,
                        NULL, NULL, '[]', NULL,
                        0, 0, 0, 0, FALSE, 'collected',
                        'wp', %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        title,
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                        to_dzen,
                        to_instagram,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

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
    ) -> Dict:
        """Создает пост Telegram в таблице tg_posts.
        
        Args:
            user_id: ID пользователя
            text: Текст поста (до 4096 символов)
            images: Список URL изображений
            to_*: цели дублирования в другие сети
        
        Returns:
            Созданный пост из таблицы tg_posts
        """
        # Проверка лимита символов для Telegram
        limit = self.PLATFORM_LIMITS.get("tg", 4096)
        if len(text) > limit:
            raise ValueError(f"Text exceeds tg limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tg_posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    ) VALUES (
                        %s, %s, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, %s, NULL,
                        0, 0, 0, 0, FALSE, 'collected',
                        'tg', %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        json.dumps(images or []),
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                        to_dzen,
                        to_instagram,
                    )
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

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
        **kwargs,
    ) -> Dict:
        """Создаёт ручной пост в cpost_posts (далее collector переносит в posts)."""
        limit = self.PLATFORM_LIMITS.get("cpost", 150000)
        if len(text) > limit:
            raise ValueError(f"Text exceeds cpost limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO cpost_posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s::jsonb, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                        json.dumps(kwargs.get("images") or []),
                        kwargs.get("image_over_text"),
                        kwargs.get("comments", 0),
                        kwargs.get("reposts", 0),
                        kwargs.get("likes", 0),
                        kwargs.get("views", 0),
                        kwargs.get("is_ad", False),
                        status,
                        "cpost",
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_dzen,
                        to_instagram,
                        to_threads,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

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
    ) -> Dict:
        """Создаёт пост Twitter в tw_posts (далее collector переносит в posts)."""
        limit = self.PLATFORM_LIMITS.get("tw", 280)
        if len(text) > limit:
            raise ValueError(f"Text exceeds tw limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tw_posts (
                        user_id, post_text, status, post_type,
                        to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    ) VALUES (
                        %s, %s, 'collected', 'tw',
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                        to_dzen,
                        to_instagram,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_tw_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Посты пользователя из tw_posts (очередь / история)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM tw_posts
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_cpost_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Список ручных постов из cpost_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT * FROM cpost_posts
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_cpost_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Один ручной пост по id в cpost_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM cpost_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_cpost_post(
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
        """Обновляет cpost_posts и дублирует изменения в posts, если строка уже собрана collector."""
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
                if to_tg is not None:
                    updates.append("to_tg = %s")
                    params.append(to_tg)
                if to_tw is not None:
                    updates.append("to_tw = %s")
                    params.append(to_tw)
                if to_wp is not None:
                    updates.append("to_wp = %s")
                    params.append(to_wp)
                if to_vk is not None:
                    updates.append("to_vk = %s")
                    params.append(to_vk)
                if to_threads is not None:
                    updates.append("to_threads = %s")
                    params.append(to_threads)
                if to_dzen is not None:
                    updates.append("to_dzen = %s")
                    params.append(to_dzen)
                if to_instagram is not None:
                    updates.append("to_instagram = %s")
                    params.append(to_instagram)
                if not updates:
                    return await self.get_cpost_post(user_id, post_id)
                params.extend([user_id, post_id])
                query = f"""
                    UPDATE cpost_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                """
                await cur.execute(query, params)
                row = await cur.fetchone()
                if not row:
                    return None

                mirror_updates = []
                mirror_params = []
                if title is not None:
                    mirror_updates.append("title = %s")
                    mirror_params.append(title)
                if post_text is not None:
                    mirror_updates.append("post_text = %s")
                    mirror_params.append(post_text)
                if domain is not None:
                    mirror_updates.append("domain = %s")
                    mirror_params.append(domain)
                if url is not None:
                    mirror_updates.append("url = %s")
                    mirror_params.append(url)
                if author is not None:
                    mirror_updates.append("author = %s")
                    mirror_params.append(author)
                if avatar is not None:
                    mirror_updates.append("avatar = %s")
                    mirror_params.append(avatar)
                if post_date is not None:
                    mirror_updates.append("post_date = %s")
                    mirror_params.append(post_date)
                if screenshot is not None:
                    mirror_updates.append("screenshot = %s")
                    mirror_params.append(screenshot)
                if images is not None:
                    mirror_updates.append("images = %s")
                    mirror_params.append(json.dumps(images))
                if image_over_text is not None:
                    mirror_updates.append("image_over_text = %s")
                    mirror_params.append(image_over_text)
                if comments is not None:
                    mirror_updates.append("comments = %s")
                    mirror_params.append(comments)
                if reposts is not None:
                    mirror_updates.append("reposts = %s")
                    mirror_params.append(reposts)
                if likes is not None:
                    mirror_updates.append("likes = %s")
                    mirror_params.append(likes)
                if views is not None:
                    mirror_updates.append("views = %s")
                    mirror_params.append(views)
                if is_ad is not None:
                    mirror_updates.append("is_ad = %s")
                    mirror_params.append(is_ad)
                if status is not None:
                    mirror_updates.append("status = %s")
                    mirror_params.append(status)
                if to_tg is not None:
                    mirror_updates.append("to_tg = %s")
                    mirror_params.append(to_tg)
                if to_tw is not None:
                    mirror_updates.append("to_tw = %s")
                    mirror_params.append(to_tw)
                if to_wp is not None:
                    mirror_updates.append("to_wp = %s")
                    mirror_params.append(to_wp)
                if to_vk is not None:
                    mirror_updates.append("to_vk = %s")
                    mirror_params.append(to_vk)
                if to_threads is not None:
                    mirror_updates.append("to_threads = %s")
                    mirror_params.append(to_threads)
                if to_dzen is not None:
                    mirror_updates.append("to_dzen = %s")
                    mirror_params.append(to_dzen)
                if to_instagram is not None:
                    mirror_updates.append("to_instagram = %s")
                    mirror_params.append(to_instagram)
                if mirror_updates:
                    sync_params = list(mirror_params)
                    sync_params.extend([user_id, "cpost", post_id])
                    await cur.execute(
                        f"""
                        UPDATE posts SET {", ".join(mirror_updates)}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND source_platform = %s AND source_id = %s
                        """,
                        sync_params,
                    )
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def delete_cpost_post(self, user_id: int, post_id: int) -> bool:
        """Удаляет зеркало в posts и строку в cpost_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM posts
                    WHERE user_id = %s AND source_platform = %s AND source_id = %s
                    """,
                    (user_id, "cpost", post_id),
                )
                await cur.execute(
                    "DELETE FROM cpost_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)
    
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
            platform: Фильтр по платформе (to_tg, to_tw, ...)
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
                    field_map = {
                        "tg": "to_tg",
                        "tw": "to_tw",
                        "wp": "to_wp",
                        "vk": "to_vk",
                    }
                    if platform in field_map:
                        query += f" AND {field_map[platform]} = TRUE"
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                return [self._row_to_post(row, cur.description) for row in rows]
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
                    return self._row_to_post(row, cur.description)
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
                    conditions.append("user_id = %s")
                    params.append(user_id)
                if status:
                    conditions.append("status = %s")
                    params.append(status)
                where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
                params.extend([limit, offset])
                await cur.execute(
                    f"SELECT * FROM posts {where} ORDER BY id DESC LIMIT %s OFFSET %s",
                    params,
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
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
                if to_tg is not None:
                    updates.append("to_tg = %s")
                    params.append(to_tg)
                if to_tw is not None:
                    updates.append("to_tw = %s")
                    params.append(to_tw)
                if to_wp is not None:
                    updates.append("to_wp = %s")
                    params.append(to_wp)
                if to_vk is not None:
                    updates.append("to_vk = %s")
                    params.append(to_vk)
                if to_threads is not None:
                    updates.append("to_threads = %s")
                    params.append(to_threads)
                if not updates:
                    return await self.get_post(user_id, post_id)
                params.extend([user_id, post_id])
                query = f"""
                    UPDATE posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                """
                await cur.execute(query, params)
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
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
        """Получает посты WordPress пользователя из таблицы wp_posts.
        
        Args:
            user_id: ID пользователя
            limit: Лимит записей
            offset: Смещение
        
        Returns:
            Список постов WordPress
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM wp_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_wp_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост WordPress по id.

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
                    """
                    SELECT * FROM wp_posts
                    WHERE user_id = %s AND id = %s
                    """,
                    (user_id, post_id)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_wp_post(
        self,
        user_id: int,
        post_id: int,
        title: Optional[str] = None,
        post_text: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост WordPress.

        Args:
            user_id: ID пользователя
            post_id: ID поста
            title: Заголовок
            post_text: Текст поста (content)
            status: Статус (draft, publish, pending, private, collected, etc.)

        Returns:
            Обновленный пост или None
        """
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
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_wp_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE wp_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

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
        offset: int = 0
    ) -> List[Dict]:
        """Получает посты Telegram пользователя из таблицы tg_posts.
        
        Args:
            user_id: ID пользователя
            limit: Лимит записей
            offset: Смещение
        
        Returns:
            Список постов Telegram
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM tg_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_tg_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост Telegram по id.

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
                    """
                    SELECT * FROM tg_posts
                    WHERE user_id = %s AND id = %s
                    """,
                    (user_id, post_id)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_tg_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост Telegram.

        Args:
            user_id: ID пользователя
            post_id: ID поста
            text: Текст поста
            images: Список URL изображений
            status: Статус (collected, processed, published, deleted, etc.)

        Returns:
            Обновленный пост или None
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if text is not None:
                    # Проверка лимита символов для Telegram
                    limit = self.PLATFORM_LIMITS.get("tg", 4096)
                    if len(text) > limit:
                        raise ValueError(f"Text exceeds tg limit of {limit} characters")
                    updates.append("post_text = %s")
                    params.append(text)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_tg_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE tg_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def delete_tg_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Telegram как удаленный (status = 'deleted').

        Args:
            user_id: ID пользователя
            post_id: ID поста

        Returns:
            Обновленный пост или None
        """
        return await self.update_tg_post(user_id, post_id, status="deleted")

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
    ) -> Dict:
        """Создает пост Threads в таблице threads_posts."""
        limit = self.PLATFORM_LIMITS.get("threads", 500)
        if len(text) > limit:
            raise ValueError(f"Text exceeds threads limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO threads_posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_threads
                    ) VALUES (
                        %s, %s, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, %s, NULL,
                        0, 0, 0, 0, FALSE, 'collected',
                        'threads', %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        json.dumps(images or []),
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_threads_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Получает посты Threads пользователя из таблицы threads_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM threads_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_threads_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост Threads по id."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM threads_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_threads_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост Threads."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if text is not None:
                    limit = self.PLATFORM_LIMITS.get("threads", 500)
                    if len(text) > limit:
                        raise ValueError(f"Text exceeds threads limit of {limit} characters")
                    updates.append("post_text = %s")
                    params.append(text)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_threads_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE threads_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params,
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

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
    ) -> Dict:
        """Создаёт пост VKontakte в таблице vk_posts (status=created; collector переносит в posts, затем pipeline до ready для публикации)."""
        limit = self.PLATFORM_LIMITS.get("vk", 15985)
        if len(text) > limit:
            raise ValueError(f"Text exceeds vk limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        images = images or []
        # Для постов с картинками vk-bot использует upload.photo_wall; явно задаём attachments с type=photo
        attachments = [{"type": "photo", "path": p} for p in images] if images else []
        images_json = json.dumps(images)
        attachments_json = json.dumps(attachments)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_posts (
                        user_id, post_text, images, attachments,
                        status, post_type, to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    ) VALUES (
                        %s, %s, %s, %s,
                        'created', 'vk', %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        images_json,
                        attachments_json,
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_threads,
                        to_dzen,
                        to_instagram,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_vk_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Получает посты VKontakte пользователя из таблицы vk_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM vk_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_vk_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост VKontakte по id."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM vk_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id)
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_vk_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List] = None,
        attachments: Optional[List] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост VKontakte."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if text is not None:
                    limit = self.PLATFORM_LIMITS.get("vk", 15985)
                    if len(text) > limit:
                        raise ValueError(f"Text exceeds vk limit of {limit} characters")
                    updates.append("post_text = %s")
                    params.append(text)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if attachments is not None:
                    updates.append("attachments = %s")
                    params.append(json.dumps(attachments))
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_vk_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE vk_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def delete_vk_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост VKontakte как удаленный (status = 'deleted')."""
        return await self.update_vk_post(user_id, post_id, status="deleted")

    async def get_url_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Получает посты из url_posts пользователя (собранные по URL).
        
        Args:
            user_id: ID пользователя
            limit: Лимит записей
            offset: Смещение
        
        Returns:
            Список постов из url_posts
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, url, post_text, images, status, post_date,
                           to_tg, to_tw, to_wp, to_vk, created_at, updated_at
                    FROM url_posts
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)
    
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
    
    def _row_to_post(self, row, description) -> Dict:
        """Преобразует строку БД в словарь поста."""
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
    ) -> Dict:
        """Создает пост Дзен в таблице dzen_posts."""
        limit = self.PLATFORM_LIMITS.get("dzen", 1500)
        if len(text) > limit:
            raise ValueError(f"Text exceeds dzen limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO dzen_posts (
                        user_id, post_text, title, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text, videos,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_threads, to_instagram
                    ) VALUES (
                        %s, %s, %s, NULL, NULL, NULL, NULL,
                        NULL, NULL, %s, NULL, %s,
                        0, 0, 0, 0, FALSE, 'collected',
                        'dzen', %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        text,
                        title,
                        json.dumps(images or []),
                        json.dumps(videos or []),
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_dzen,
                        to_threads,
                        to_instagram,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_dzen_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Получает посты Дзен пользователя из таблицы dzen_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM dzen_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_dzen_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост Дзен по id."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM dzen_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_dzen_post(
        self,
        user_id: int,
        post_id: int,
        text: Optional[str] = None,
        title: Optional[str] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост Дзен."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if text is not None:
                    limit = self.PLATFORM_LIMITS.get("dzen", 1500)
                    if len(text) > limit:
                        raise ValueError(f"Text exceeds dzen limit of {limit} characters")
                    updates.append("post_text = %s")
                    params.append(text)
                if title is not None:
                    updates.append("title = %s")
                    params.append(title)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if videos is not None:
                    updates.append("videos = %s")
                    params.append(json.dumps(videos))
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_dzen_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE dzen_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params,
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

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
    ) -> Dict:
        """Создает пост Instagram в таблице instagram_posts (status=ready для ручной публикации)."""
        limit = self.PLATFORM_LIMITS.get("instagram", 2200)
        if len(caption) > limit:
            raise ValueError(f"Caption exceeds instagram limit of {limit} characters")

        await ensure_monthly_post_quota(user_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO instagram_posts (
                        user_id, post_text, domain, url, author, avatar,
                        post_date, screenshot, images, image_over_text, videos,
                        comments, reposts, likes, views, is_ad, status,
                        post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_threads, to_instagram
                    ) VALUES (
                        %s, %s, NULL, NULL, NULL, NULL,
                        NULL, NULL, %s, NULL, %s,
                        0, 0, 0, 0, FALSE, 'ready',
                        'instagram', %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        user_id,
                        caption,
                        json.dumps(images or []),
                        json.dumps(videos or []),
                        to_tg,
                        to_tw,
                        to_wp,
                        to_vk,
                        to_dzen,
                        to_threads,
                        to_instagram,
                    ),
                )
                row = await cur.fetchone()
                return self._row_to_post(row, cur.description)
        finally:
            await release_db_connection(conn)

    async def get_instagram_posts(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Получает посты Instagram пользователя из таблицы instagram_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM instagram_posts
                    WHERE user_id = %s AND (status IS NULL OR status != 'deleted')
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = await cur.fetchall()
                return [self._row_to_post(row, cur.description) for row in rows]
        finally:
            await release_db_connection(conn)

    async def get_instagram_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Получает один пост Instagram по id."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM instagram_posts WHERE user_id = %s AND id = %s",
                    (user_id, post_id),
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def update_instagram_post(
        self,
        user_id: int,
        post_id: int,
        caption: Optional[str] = None,
        images: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Обновляет пост Instagram."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                updates = []
                params = []
                if caption is not None:
                    limit = self.PLATFORM_LIMITS.get("instagram", 2200)
                    if len(caption) > limit:
                        raise ValueError(f"Caption exceeds instagram limit of {limit} characters")
                    updates.append("post_text = %s")
                    params.append(caption)
                if images is not None:
                    updates.append("images = %s")
                    params.append(json.dumps(images))
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                if not updates:
                    return await self.get_instagram_post(user_id, post_id)
                params.extend([user_id, post_id])
                await cur.execute(
                    f"""
                    UPDATE instagram_posts SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND id = %s
                    RETURNING *
                    """,
                    params,
                )
                row = await cur.fetchone()
                if row:
                    return self._row_to_post(row, cur.description)
                return None
        finally:
            await release_db_connection(conn)

    async def delete_instagram_post(self, user_id: int, post_id: int) -> Optional[Dict]:
        """Помечает пост Instagram как удаленный (status = 'deleted')."""
        return await self.update_instagram_post(user_id, post_id, status="deleted")


post_service = PostService()

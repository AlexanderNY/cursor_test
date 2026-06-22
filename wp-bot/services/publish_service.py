"""Сервис для публикации постов в WordPress."""

import logging
from typing import Dict, Any, List, Optional

from config import settings
from database import get_db_connection, release_db_connection
from services.wordpress_client import WordPressClient

logger = logging.getLogger(__name__)


class PublishService:
    """Сервис для публикации постов из wp_posts в WordPress."""
    
    async def publish_pending_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Публикует посты из wp_posts в WordPress.
        
        Args:
            user_id: ID пользователя для фильтрации (опционально)
            
        Returns:
            Словарь с результатами публикации
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                # Получаем посты для публикации (статус ready)
                limit = settings.PUBLISH_POSTS_LIMIT
                if user_id:
                    await cur.execute(
                        """
                        SELECT * FROM wp_posts
                        WHERE user_id = %s
                          AND status = 'ready'
                          AND to_wp = TRUE
                        ORDER BY created_at ASC
                        LIMIT %s
                        """,
                        (user_id, limit)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT * FROM wp_posts
                        WHERE status = 'ready'
                          AND to_wp = TRUE
                        ORDER BY created_at ASC
                        LIMIT %s
                        """,
                        (limit,)
                    )
                
                rows = await cur.fetchall()
                if not rows:
                    return {"published": 0, "failed": 0, "errors": []}
                
                # Получаем описание колонок
                columns = [col.name for col in cur.description]
                
                published_count = 0
                failed_count = 0
                errors = []
                
                # Группируем посты по user_id для получения профилей
                posts_by_user: Dict[int, List[Dict]] = {}
                for row in rows:
                    post = dict(zip(columns, row))
                    user_id_post = post["user_id"]
                    if user_id_post not in posts_by_user:
                        posts_by_user[user_id_post] = []
                    posts_by_user[user_id_post].append(post)
                
                # Обрабатываем посты для каждого пользователя
                for uid, posts in posts_by_user.items():
                    try:
                        # Получаем профиль пользователя
                        await cur.execute(
                            "SELECT * FROM wp_profiles WHERE user_id = %s",
                            (uid,)
                        )
                        profile_row = await cur.fetchone()
                        
                        if not profile_row:
                            logger.warning(f"Profile not found for user_id={uid}")
                            for post in posts:
                                await self._update_post_status(
                                    cur, post["id"], "failed",
                                    f"Profile not found for user_id={uid}"
                                )
                                failed_count += 1
                            continue
                        
                        profile_columns = [col.name for col in cur.description]
                        profile = dict(zip(profile_columns, profile_row))
                        
                        # Проверяем наличие credentials
                        if not profile.get("site_url") or not profile.get("username") or not profile.get("app_password"):
                            logger.warning(f"Incomplete profile for user_id={uid}")
                            for post in posts:
                                await self._update_post_status(
                                    cur, post["id"], "failed",
                                    "Incomplete WordPress profile credentials"
                                )
                                failed_count += 1
                            continue
                        
                        # Создаем WordPress клиент
                        wp_client = WordPressClient(
                            site_url=profile["site_url"],
                            username=profile["username"],
                            app_password=profile["app_password"]
                        )
                        
                        # Публикуем каждый пост
                        for post in posts:
                            try:
                                # Подготавливаем данные для публикации
                                title = post.get("title") or "Untitled"
                                content = post.get("post_text") or ""
                                
                                if not content:
                                    await self._update_post_status(
                                        cur, post["id"], "failed",
                                        "Post content is empty"
                                    )
                                    failed_count += 1
                                    continue
                                
                                # Публикуем пост
                                wp_post = await wp_client.create_post(
                                    title=title,
                                    content=content,
                                    status="publish"
                                )
                                
                                # Обновляем статус поста
                                wp_post_id = wp_post.get("id")
                                wp_post_link = wp_post.get("link", "")
                                
                                await cur.execute(
                                    """
                                    UPDATE wp_posts
                                    SET status = 'published',
                                        url = %s,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = %s
                                    """,
                                    (wp_post_link, post["id"])
                                )
                                
                                published_count += 1
                                logger.info(
                                    f"Published post {post['id']} to WordPress "
                                    f"(wp_post_id={wp_post_id}, user_id={uid})"
                                )
                                
                            except Exception as e:
                                error_msg = str(e)
                                logger.error(
                                    f"Failed to publish post {post['id']} "
                                    f"(user_id={uid}): {error_msg}"
                                )
                                await self._update_post_status(
                                    cur, post["id"], "failed", error_msg
                                )
                                errors.append({
                                    "post_id": post["id"],
                                    "user_id": uid,
                                    "error": error_msg
                                })
                                failed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing user_id={uid}: {str(e)}"
                        logger.error(error_msg)
                        for post in posts:
                            await self._update_post_status(
                                cur, post["id"], "failed", error_msg
                            )
                            failed_count += 1
                        errors.append({
                            "user_id": uid,
                            "error": error_msg
                        })
                
                await conn.commit()
                
                return {
                    "published": published_count,
                    "failed": failed_count,
                    "errors": errors
                }
        finally:
            await release_db_connection(conn)
    
    async def _update_post_status(
        self,
        cursor,
        post_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Обновляет статус поста."""
        await cursor.execute(
            """
            UPDATE wp_posts
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (status, post_id)
        )


publish_service = PublishService()

"""Сервис для сбора постов из WordPress."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import settings
from database import get_db_connection, release_db_connection
from services.wordpress_client import WordPressClient

logger = logging.getLogger(__name__)


class CollectService:
    """Сервис для сбора постов из WordPress в wp_posts."""
    
    async def collect_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Собирает посты из WordPress и сохраняет в wp_posts.
        
        Args:
            user_id: ID пользователя для фильтрации (опционально)
            
        Returns:
            Словарь с результатами сбора
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                # Получаем профили с включенным сбором
                if user_id:
                    await cur.execute(
                        """
                        SELECT * FROM wp_profiles
                        WHERE user_id = %s
                          AND collect_enabled = TRUE
                        """,
                        (user_id,)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT * FROM wp_profiles
                        WHERE collect_enabled = TRUE
                        """
                    )
                
                profile_rows = await cur.fetchall()
                if not profile_rows:
                    return {"collected": 0, "failed": 0, "errors": []}
                
                profile_columns = [col.name for col in cur.description]
                
                collected_count = 0
                failed_count = 0
                errors = []
                limit_per_pass = settings.COLLECT_POSTS_LIMIT
                
                # Обрабатываем каждый профиль (общий лимит постов за проход)
                for profile_row in profile_rows:
                    if collected_count >= limit_per_pass:
                        break
                    profile = dict(zip(profile_columns, profile_row))
                    uid = profile["user_id"]
                    
                    try:
                        # Проверяем наличие credentials
                        if not profile.get("site_url") or not profile.get("username") or not profile.get("app_password"):
                            logger.warning(f"Incomplete profile for user_id={uid}")
                            errors.append({
                                "user_id": uid,
                                "error": "Incomplete WordPress profile credentials"
                            })
                            failed_count += 1
                            continue
                        
                        # Создаем WordPress клиент
                        wp_client = WordPressClient(
                            site_url=profile["site_url"],
                            username=profile["username"],
                            app_password=profile["app_password"]
                        )
                        
                        # Получаем последний собранный пост для этого пользователя
                        await cur.execute(
                            """
                            SELECT MAX(created_at) as last_collected
                            FROM wp_posts
                            WHERE user_id = %s
                              AND post_type = 'wp'
                            """,
                            (uid,)
                        )
                        last_row = await cur.fetchone()
                        last_collected = last_row[0] if last_row and last_row[0] else None
                        
                        # Получаем посты из WordPress (лимит за проход из config)
                        page = 1
                        per_page = 20
                        total_collected_for_user = 0
                        remaining = limit_per_pass - collected_count
                        
                        while remaining > 0:
                            try:
                                # Получаем посты
                                result = await wp_client.get_posts(
                                    per_page=per_page,
                                    page=page,
                                    status="publish"
                                )
                                
                                posts = result.get("posts", [])
                                if not posts:
                                    break
                                
                                # Сохраняем посты в БД
                                for wp_post in posts:
                                    if collected_count >= limit_per_pass:
                                        break
                                    # Проверяем, не был ли уже собран этот пост
                                    wp_post_id = wp_post.get("id")
                                    wp_post_link = wp_post.get("link", "")
                                    
                                    await cur.execute(
                                        """
                                        SELECT id FROM wp_posts
                                        WHERE user_id = %s
                                          AND url = %s
                                        """,
                                        (uid, wp_post_link)
                                    )
                                    existing = await cur.fetchone()
                                    
                                    if existing:
                                        # Пост уже существует, пропускаем
                                        continue
                                    
                                    # Парсим дату публикации
                                    post_date = None
                                    if wp_post.get("date"):
                                        try:
                                            post_date = datetime.fromisoformat(
                                                wp_post["date"].replace("Z", "+00:00")
                                            )
                                        except:
                                            pass
                                    
                                    # Извлекаем данные поста
                                    title = wp_post.get("title", {}).get("rendered", "") if isinstance(wp_post.get("title"), dict) else wp_post.get("title", "")
                                    content = wp_post.get("content", {}).get("rendered", "") if isinstance(wp_post.get("content"), dict) else wp_post.get("content", "")
                                    
                                    # Извлекаем автора
                                    author_name = None
                                    if wp_post.get("_embedded") and wp_post["_embedded"].get("author"):
                                        author_data = wp_post["_embedded"]["author"][0]
                                        author_name = author_data.get("name")
                                    
                                    # Сохраняем пост
                                    await cur.execute(
                                        """
                                        INSERT INTO wp_posts (
                                            user_id, domain, url, title, author,
                                            post_date, post_text, status, post_type,
                                            to_wp, created_at, updated_at
                                        ) VALUES (
                                            %s, %s, %s, %s, %s,
                                            %s, %s, %s, %s,
                                            TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                                        )
                                        """,
                                        (
                                            uid,
                                            profile.get("site_url"),
                                            wp_post_link,
                                            title,
                                            author_name,
                                            post_date,
                                            content,
                                            "collected",
                                            "wp"
                                        )
                                    )
                                    
                                    total_collected_for_user += 1
                                    collected_count += 1
                                
                                # Проверяем, есть ли еще страницы
                                total_pages = result.get("total_pages", 0)
                                if page >= total_pages:
                                    break
                                
                                remaining = limit_per_pass - collected_count
                                page += 1
                                
                            except Exception as e:
                                error_msg = f"Error fetching posts page {page} for user_id={uid}: {str(e)}"
                                logger.error(error_msg)
                                errors.append({
                                    "user_id": uid,
                                    "page": page,
                                    "error": error_msg
                                })
                                break
                        
                        if total_collected_for_user > 0:
                            logger.info(
                                f"Collected {total_collected_for_user} posts from WordPress "
                                f"for user_id={uid}"
                            )
                        
                    except Exception as e:
                        error_msg = f"Error processing user_id={uid}: {str(e)}"
                        logger.error(error_msg)
                        errors.append({
                            "user_id": uid,
                            "error": error_msg
                        })
                        failed_count += 1
                
                await conn.commit()
                
                return {
                    "collected": collected_count,
                    "failed": failed_count,
                    "errors": errors
                }
        finally:
            await release_db_connection(conn)


collect_service = CollectService()

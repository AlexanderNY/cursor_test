"""Сервис для сбора статистики постов."""

from typing import List, Dict, Optional
from database import get_db_connection, release_db_connection


class StatisticsService:
    """Сервис для получения статистики по постам."""
    
    async def get_statistics(self) -> List[Dict]:
        """Собирает статистику по постам для каждой платформы.
        
        Returns:
            Список статистики по платформам
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                # Статистика для Telegram
                tg_stats = await self._get_platform_stats(cur, "to_tg", "Telegram")
                
                # Статистика для Twitter
                tw_stats = await self._get_platform_stats(cur, "to_tw", "Twitter")
                
                # Статистика для WordPress
                wp_stats = await self._get_platform_stats(cur, "to_wp", "WordPress")
                
                # Статистика для VKontakte
                vk_stats = await self._get_platform_stats(cur, "to_vk", "VKontakte")
                
                # Общая статистика
                total_stats = await self._get_total_stats(cur)
                
                return [tg_stats, tw_stats, wp_stats, vk_stats, total_stats]
        finally:
            await release_db_connection(conn)
    
    async def _get_platform_stats(self, cur, platform_field: str, platform_name: str) -> Dict:
        """Получает статистику для конкретной платформы.
        
        Args:
            cur: Курсор БД
            platform_field: Поле платформы (to_tg, to_tw и т.д.)
            platform_name: Название платформы
            
        Returns:
            Словарь со статистикой
        """
        # Собранные посты
        await cur.execute(f"""
            SELECT COUNT(*) FROM posts 
            WHERE {platform_field} = TRUE AND status = 'collected'
        """)
        collected = (await cur.fetchone())[0]
        
        # Обработанные посты
        await cur.execute(f"""
            SELECT COUNT(*) FROM posts 
            WHERE {platform_field} = TRUE AND status = 'processed'
        """)
        processed = (await cur.fetchone())[0]
        
        # Опубликованные посты
        await cur.execute(f"""
            SELECT COUNT(*) FROM posts 
            WHERE {platform_field} = TRUE AND status = 'published'
        """)
        published = (await cur.fetchone())[0]
        
        return {
            "service_name": platform_name,
            "collected_posts": collected,
            "processed_posts": processed,
            "published_posts": published
        }
    
    async def _get_total_stats(self, cur) -> Dict:
        """Получает общую статистику по всем постам.
        
        Args:
            cur: Курсор БД
            
        Returns:
            Словарь с общей статистикой
        """
        await cur.execute("SELECT COUNT(*) FROM posts WHERE status = 'collected'")
        collected = (await cur.fetchone())[0]
        
        await cur.execute("SELECT COUNT(*) FROM posts WHERE status = 'processed'")
        processed = (await cur.fetchone())[0]
        
        await cur.execute("SELECT COUNT(*) FROM posts WHERE status = 'published'")
        published = (await cur.fetchone())[0]
        
        return {
            "service_name": "Total",
            "collected_posts": collected,
            "processed_posts": processed,
            "published_posts": published
        }
    
    async def get_users_statistics(self, user_ids: Optional[List[int]] = None) -> List[Dict]:
        """Собирает статистику использования по пользователям.
        
        Args:
            user_ids: если задан, возвращает статистику только по этим user_id; иначе по всем.
        
        Returns:
            Список статистики по пользователям
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if user_ids is not None and len(user_ids) == 0:
                    return []
                if user_ids is not None:
                    placeholders = ",".join(["%s"] * len(user_ids))
                    await cur.execute(
                        f"""
                        SELECT 
                            user_id,
                            COUNT(*) as total_posts,
                            COUNT(*) FILTER (WHERE status = 'collected') as collected_posts,
                            COUNT(*) FILTER (WHERE status = 'processed') as processed_posts,
                            COUNT(*) FILTER (WHERE status = 'published') as published_posts
                        FROM posts
                        WHERE user_id IN ({placeholders})
                        GROUP BY user_id
                        ORDER BY total_posts DESC
                        """,
                        tuple(user_ids),
                    )
                else:
                    await cur.execute("""
                        SELECT 
                            user_id,
                            COUNT(*) as total_posts,
                            COUNT(*) FILTER (WHERE status = 'collected') as collected_posts,
                            COUNT(*) FILTER (WHERE status = 'processed') as processed_posts,
                            COUNT(*) FILTER (WHERE status = 'published') as published_posts
                        FROM posts
                        GROUP BY user_id
                        ORDER BY total_posts DESC
                    """)
                rows = await cur.fetchall()
                return [
                    {
                        "user_id": row[0],
                        "total_posts": row[1],
                        "collected_posts": row[2],
                        "processed_posts": row[3],
                        "published_posts": row[4]
                    }
                    for row in rows
                ]
        finally:
            await release_db_connection(conn)


statistics_service = StatisticsService()

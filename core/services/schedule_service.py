"""Сервис для работы с расписаниями из schedule_snapshots."""

import json
from typing import List, Dict, Any
from database import get_db_connection, release_db_connection


class ScheduleService:
    """Сервис для получения расписаний из таблицы schedule_snapshots."""
    
    async def get_schedule_snapshots(self) -> List[Dict[str, Any]]:
        """Получает все записи из таблицы schedule_snapshots.
        
        Returns:
            Список записей расписаний
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, platform, publish_enabled, collect_enabled,
                           schedule_type, time_intervals, updated_at
                    FROM schedule_snapshots
                    ORDER BY user_id, platform
                    """
                )
                rows = await cur.fetchall()
                
                result = []
                for row in rows:
                    user_id, platform, publish_enabled, collect_enabled, schedule_type, time_intervals, updated_at = row
                    
                    # Парсим time_intervals если это строка
                    if isinstance(time_intervals, str):
                        try:
                            time_intervals = json.loads(time_intervals) if time_intervals else []
                        except json.JSONDecodeError:
                            time_intervals = []
                    
                    result.append({
                        "user_id": user_id,
                        "platform": platform,
                        "publish_enabled": bool(publish_enabled),
                        "collect_enabled": bool(collect_enabled),
                        "schedule_type": schedule_type or "immediate",
                        "time_intervals": time_intervals if isinstance(time_intervals, list) else [],
                        "updated_at": updated_at
                    })
                
                return result
        finally:
            await release_db_connection(conn)


schedule_service = ScheduleService()

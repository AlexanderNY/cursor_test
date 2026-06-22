"""Роутер для обработки команд от scheduler."""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from services.publish_service import publish_service
from services.collect_service import collect_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Schedule"])


class ScheduleItem(BaseModel):
    """Модель расписания от scheduler."""
    user_id: int
    platform: str
    publish_enabled: bool
    collect_enabled: bool
    schedule_type: str
    time_intervals: List[Dict[str, Any]]


class ScheduleRequest(BaseModel):
    """Модель запроса от scheduler."""
    schedules: List[ScheduleItem]


@router.post("/schedule")
async def handle_schedule(request: ScheduleRequest) -> Dict[str, Any]:
    """
    Обрабатывает команды от scheduler.
    
    Args:
        request: Запрос с расписаниями
        
    Returns:
        Результаты обработки
    """
    # Фильтруем расписания по platform="wp"
    wp_schedules = [
        s for s in request.schedules
        if s.platform == "wp"
    ]
    
    if not wp_schedules:
        return {
            "status": "ok",
            "message": "No WordPress schedules found",
            "publish_result": None,
            "collect_result": None
        }
    
    logger.info(f"Received {len(wp_schedules)} WordPress schedules")
    
    # Определяем, нужно ли публиковать или собирать
    should_publish = any(s.publish_enabled for s in wp_schedules)
    should_collect = any(s.collect_enabled for s in wp_schedules)
    
    publish_result = None
    collect_result = None
    
    # Публикация постов
    if should_publish:
        try:
            # Если есть конкретные user_id, публикуем для них
            user_ids = [s.user_id for s in wp_schedules if s.publish_enabled]
            if len(user_ids) == 1:
                publish_result = await publish_service.publish_pending_posts(
                    user_id=user_ids[0]
                )
            else:
                # Публикуем для всех пользователей
                publish_result = await publish_service.publish_pending_posts()
            
            logger.info(
                f"Publish completed: {publish_result.get('published', 0)} published, "
                f"{publish_result.get('failed', 0)} failed"
            )
        except Exception as e:
            logger.error(f"Error during publish: {str(e)}")
            publish_result = {
                "published": 0,
                "failed": 0,
                "errors": [str(e)]
            }
    
    # Сбор постов
    if should_collect:
        try:
            # Если есть конкретные user_id, собираем для них
            user_ids = [s.user_id for s in wp_schedules if s.collect_enabled]
            if len(user_ids) == 1:
                collect_result = await collect_service.collect_posts(
                    user_id=user_ids[0]
                )
            else:
                # Собираем для всех пользователей
                collect_result = await collect_service.collect_posts()
            
            logger.info(
                f"Collect completed: {collect_result.get('collected', 0)} collected, "
                f"{collect_result.get('failed', 0)} failed"
            )
        except Exception as e:
            logger.error(f"Error during collect: {str(e)}")
            collect_result = {
                "collected": 0,
                "failed": 0,
                "errors": [str(e)]
            }
    
    return {
        "status": "ok",
        "message": "Schedule processed",
        "publish_result": publish_result,
        "collect_result": collect_result
    }

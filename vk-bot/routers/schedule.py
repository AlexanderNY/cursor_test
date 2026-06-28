"""Роутер для обработки команд от scheduler."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from services.post_collector import PostCollector
from services.post_publisher import PostPublisher


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Schedule"])

_post_collector = PostCollector()
_post_publisher = PostPublisher()


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
    """Обрабатывает команды от scheduler для platform=vk."""
    vk_schedules = [s for s in request.schedules if s.platform == "vk"]

    if not vk_schedules:
        return {
            "status": "ok",
            "message": "No VK schedules found",
            "publish_result": None,
            "collect_result": None,
        }

    logger.info("Received %d VK schedules", len(vk_schedules))

    should_publish = any(s.publish_enabled for s in vk_schedules)
    should_collect = any(s.collect_enabled for s in vk_schedules)

    publish_result = None
    collect_result = None

    if should_publish:
        try:
            published = await _post_publisher.publish_ready_posts()
            publish_result = {"published": published, "failed": 0, "errors": []}
            logger.info("VK publish completed: %d published", published)
        except Exception as e:
            logger.error("Error during VK publish: %s", e, exc_info=True)
            publish_result = {"published": 0, "failed": 0, "errors": [str(e)]}

    if should_collect:
        try:
            collected = await _post_collector.run_collect()
            collect_result = {"collected": collected, "failed": 0, "errors": []}
            logger.info("VK collect completed: %d collected", collected)
        except Exception as e:
            logger.error("Error during VK collect: %s", e, exc_info=True)
            collect_result = {"collected": 0, "failed": 0, "errors": [str(e)]}

    return {
        "status": "ok",
        "message": "Schedule processed",
        "publish_result": publish_result,
        "collect_result": collect_result,
    }

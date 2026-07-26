"""Роутер schedule и управления опубликованными постами."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Schedule"])

_bot_service = None


def set_bot_service(bot_service) -> None:
    global _bot_service
    _bot_service = bot_service


class ScheduleItem(BaseModel):
    user_id: int
    platform: str
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: str = "immediate"
    time_intervals: List[Dict[str, Any]] = Field(default_factory=list)


class ScheduleRequest(BaseModel):
    schedules: List[ScheduleItem] = Field(default_factory=list)


class EditPublishedRequest(BaseModel):
    user_id: int
    text: str = Field(..., min_length=1, max_length=4096)


class DeletePublishedRequest(BaseModel):
    user_id: int


@router.post("/schedule")
async def handle_schedule(request: ScheduleRequest) -> Dict[str, Any]:
    """Обрабатывает команды от scheduler: публикует due-посты."""
    if not _bot_service or not _bot_service.post_publisher:
        return {"status": "error", "message": "Bot service not initialized"}

    tg_schedules = [s for s in request.schedules if s.platform in ("tg", "telegram")]
    should_publish = any(s.publish_enabled for s in tg_schedules) if tg_schedules else True

    publish_result = None
    if should_publish:
        try:
            published = await _bot_service.post_publisher.publish_ready_posts()
            publish_result = {"published": published, "failed": 0, "errors": []}
        except Exception as e:
            logger.error("schedule publish failed: %s", e, exc_info=True)
            publish_result = {"published": 0, "failed": 1, "errors": [str(e)]}

    upcoming = []
    try:
        upcoming = await _bot_service.post_publisher.get_upcoming_schedule(hours=24)
        # serialize datetimes
        for item in upcoming:
            for key in ("publish_at", "created_at"):
                val = item.get(key)
                if hasattr(val, "isoformat"):
                    item[key] = val.isoformat()
    except Exception as e:
        logger.warning("Failed to load upcoming schedule: %s", e)

    return {
        "status": "ok",
        "message": "Schedule processed",
        "publish_result": publish_result,
        "upcoming": upcoming,
        "schedules_received": len(tg_schedules),
    }


@router.get("/schedule/upcoming")
async def get_upcoming(hours: int = 24, user_id: Optional[int] = None) -> Dict[str, Any]:
    if not _bot_service or not _bot_service.post_publisher:
        raise HTTPException(status_code=503, detail="Bot service not initialized")
    items = await _bot_service.post_publisher.get_upcoming_schedule(hours=hours, user_id=user_id)
    for item in items:
        for key in ("publish_at", "created_at"):
            val = item.get(key)
            if hasattr(val, "isoformat"):
                item[key] = val.isoformat()
    return {"items": items}


@router.post("/published/{post_id}/edit")
async def edit_published(post_id: int, body: EditPublishedRequest) -> Dict[str, Any]:
    if not _bot_service or not _bot_service.post_publisher:
        raise HTTPException(status_code=503, detail="Bot service not initialized")
    result = await _bot_service.post_publisher.edit_published_post(
        body.user_id, post_id, body.text
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Edit failed"))
    return result


@router.post("/published/{post_id}/delete")
async def delete_published(post_id: int, body: DeletePublishedRequest) -> Dict[str, Any]:
    if not _bot_service or not _bot_service.post_publisher:
        raise HTTPException(status_code=503, detail="Bot service not initialized")
    result = await _bot_service.post_publisher.delete_published_post(body.user_id, post_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Delete failed"))
    return result

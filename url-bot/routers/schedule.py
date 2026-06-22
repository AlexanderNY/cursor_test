"""Роутер для обработки команд от scheduler."""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from schemas import ScheduleRequest
from services.scraping_service import scrape_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


class ScheduleResponse(BaseModel):
    """Ответ POST /schedule."""
    status: str = "ok"
    message: str = ""
    processed: int = 0
    errors: int = 0
    details: list[dict[str, Any]] = []


@router.post("", response_model=ScheduleResponse)
async def handle_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """
    Обрабатывает команды от scheduler.

    Фильтрует расписания по platform=="url" и collect_enabled, для каждого URL
    выполняет скрапинг (url, xpath, take_screenshot). Возвращает сводку.
    """
    url_schedules = [
        s for s in request.schedules
        if s.platform == "url" and s.collect_enabled and (s.urls or [])
    ]
    if not url_schedules:
        return ScheduleResponse(
            status="ok",
            message="No URL schedules to process",
            processed=0,
            errors=0,
        )
    processed = 0
    errors = 0
    details: list[dict[str, Any]] = []
    for schedule in url_schedules:
        user_id = schedule.user_id
        for item in schedule.urls:
            if not item.url or not item.xpath:
                continue
            result = await asyncio.to_thread(
                scrape_url,
                item.url,
                item.xpath,
                item.take_screenshot or False,
                user_id,
            )
            detail = {
                "user_id": user_id,
                "url": item.url,
                "xpath": item.xpath,
                "error": result.get("error"),
                "has_text": bool(result.get("text")),
                "has_screenshot": bool(
                    result.get("screenshot_base64") or result.get("screenshot_path")
                ),
            }
            if not result.get("error"):
                detail["text"] = result.get("text") or ""
                if result.get("screenshot_path"):
                    detail["screenshot_path"] = result["screenshot_path"]
                elif result.get("screenshot_base64"):
                    detail["screenshot_base64"] = result["screenshot_base64"]
                tsn = (item.target_social_networks or {}) if hasattr(item, "target_social_networks") else {}
                detail["to_tg"] = tsn.get("tg", False)
                detail["to_wp"] = tsn.get("wp", False)
                detail["to_tw"] = tsn.get("tw", False)
                detail["to_vk"] = tsn.get("vk", False)
            details.append(detail)
            if result.get("error"):
                errors += 1
            else:
                processed += 1
    logger.info("Schedule processed: %d URLs ok, %d errors", processed, errors)
    return ScheduleResponse(
        status="ok",
        message="Schedule processed",
        processed=processed,
        errors=errors,
        details=details,
    )

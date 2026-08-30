"""Роутер для обработки команд от scheduler."""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from schemas import ScheduleRequest, ScheduleUrlItem
from services.scraping_service import scrape_url_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


class ScheduleResponse(BaseModel):
    """Ответ POST /schedule."""
    status: str = "ok"
    message: str = ""
    processed: int = 0
    errors: int = 0
    skipped: int = 0
    details: list[dict[str, Any]] = []


def _parse_hhmm(value: Optional[str]) -> Optional[int]:
    """Парсит HH:MM в минуты от полуночи. None если пусто/невалидно."""
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw or ":" not in raw:
        return None
    try:
        parts = raw.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return hour * 60 + minute
    except (ValueError, TypeError, IndexError):
        return None


def _is_schedule_due(item: ScheduleUrlItem, now: Optional[datetime] = None) -> bool:
    """
    True если URL пора собирать.

    schedule_time пустой — всегда due (immediate).
    Иначе — текущие локальные HH:MM совпадают с schedule_time
    (одно срабатывание за минуту при poll ~60 с).
    """
    target = _parse_hhmm(item.schedule_time)
    if target is None:
        return True
    now = now or datetime.now().astimezone()
    current = now.hour * 60 + now.minute
    return current == target


@router.post("", response_model=ScheduleResponse)
async def handle_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """
    Обрабатывает команды от scheduler.

    Фильтрует расписания по platform=="url" и collect_enabled, для каждого URL
    с наступившим schedule_time выполняет скрапинг.
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
            skipped=0,
        )
    processed = 0
    errors = 0
    skipped = 0
    details: list[dict[str, Any]] = []
    now = datetime.now().astimezone()
    for schedule in url_schedules:
        user_id = schedule.user_id
        for item in schedule.urls:
            if not item.url or not item.xpath:
                continue
            if not _is_schedule_due(item, now):
                skipped += 1
                logger.debug(
                    "Skip URL (not due): user=%s url=%s schedule_time=%s now=%s",
                    user_id,
                    item.url,
                    item.schedule_time,
                    now.strftime("%H:%M"),
                )
                continue
            result = await scrape_url_async(
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
                screenshot_only = bool(getattr(item, "screenshot_only", False))
                raw_text = result.get("text") or ""
                final_text = "" if screenshot_only else raw_text
                detail["text"] = final_text
                detail["has_text"] = bool(final_text)
                detail["screenshot_only"] = screenshot_only
                if getattr(item, "id", None):
                    detail["url_item_id"] = item.id
                if result.get("screenshot_path"):
                    detail["screenshot_path"] = result["screenshot_path"]
                elif result.get("screenshot_base64"):
                    detail["screenshot_base64"] = result["screenshot_base64"]
                tsn = (item.target_social_networks or {}) if hasattr(item, "target_social_networks") else {}
                detail["to_tg"] = tsn.get("tg", False)
                detail["to_wp"] = tsn.get("wp", False)
                detail["to_tw"] = tsn.get("tw", False)
                detail["to_vk"] = tsn.get("vk", False)
                detail["target_channels"] = list(getattr(item, "target_channels", None) or [])
                detail["target_groups"] = list(getattr(item, "target_groups", None) or [])
            details.append(detail)
            if result.get("error"):
                errors += 1
            else:
                processed += 1
    logger.info(
        "Schedule processed: %d URLs ok, %d errors, %d skipped (not due)",
        processed,
        errors,
        skipped,
    )
    return ScheduleResponse(
        status="ok",
        message="Schedule processed",
        processed=processed,
        errors=errors,
        skipped=skipped,
        details=details,
    )

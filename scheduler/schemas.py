"""Pydantic-модели для Scheduler."""

from typing import Any

from pydantic import BaseModel


class TimeInterval(BaseModel):
    start: str
    end: str


class ScheduleItem(BaseModel):
    user_id: int
    platform: str
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: str = "immediate"
    time_intervals: list[dict[str, Any]] = []


class SchedulesResponse(BaseModel):
    schedules: list[ScheduleItem]


class ScheduleNotifyPayload(BaseModel):
    schedules: list[ScheduleItem]


class StartBotRequest(BaseModel):
    """Запрос на запуск ботов."""
    platforms: list[str]  # ["wp", "tg", "tw", "vk"]

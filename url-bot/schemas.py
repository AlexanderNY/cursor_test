"""Pydantic-модели для url-bot."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """Тело запроса POST /run (тестовый запуск по запросу)."""
    url: str = Field(..., description="URL страницы")
    xpath: str = Field(..., description="XPath селектор элемента")
    take_screenshot: bool = Field(False, description="Делать скриншот элемента")
    user_id: Optional[int] = Field(None, description="Если задан — сохранить скриншот в uploads/url/{user_id}/...")


class RunResponse(BaseModel):
    """Ответ POST /run."""
    text: Optional[str] = None
    screenshot_base64: Optional[str] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None


class ScheduleUrlItem(BaseModel):
    """Один URL в расписании (из core curl_settings)."""
    url: str = ""
    xpath: str = ""
    take_screenshot: bool = False
    schedule_time: Optional[str] = None
    target_social_networks: Optional[dict[str, bool]] = None
    run_once: bool = False  # выполнить один раз (после выполнения core исключает из расписания)


class ScheduleItem(BaseModel):
    """Одна запись расписания от scheduler."""
    user_id: int
    platform: str
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: str = "immediate"
    time_intervals: list[dict[str, Any]] = Field(default_factory=list)
    urls: list[ScheduleUrlItem] = Field(default_factory=list)


class ScheduleRequest(BaseModel):
    """Тело запроса POST /schedule."""
    schedules: list[ScheduleItem] = Field(default_factory=list)

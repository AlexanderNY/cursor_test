"""Pydantic-модели для Collector API."""

from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class CollectorFunction(BaseModel):
    """Описание одной функции сервиса."""
    id: str
    name_ru: str
    description: str


class HealthResponse(BaseModel):
    """Ответ healthcheck."""
    status: str
    service: str
    server_time: Optional[str] = None


class CycleResult(BaseModel):
    """Результат одного цикла сбора/распределения."""
    status: str
    message: str
    count: int
    errors: Optional[List[str]] = None


class LoopStatus(BaseModel):
    """Статус одного фонового цикла."""
    last_run_at: Optional[datetime] = None
    total_processed: int = 0
    last_cycle_count: int = 0


class ServiceStatus(BaseModel):
    """Полный статус сервиса."""
    service: str
    version: str
    collect_interval_sec: int
    distribute_interval_sec: int
    collect_batch_size: int
    distribute_batch_size: int
    collector: LoopStatus
    distributor: LoopStatus
    current_time: str = ""
    started_at: Optional[str] = None
    collect_functions: List[CollectorFunction] = []


class PlatformMetric(BaseModel):
    """Метрика по одной платформе."""
    platform: str
    table: str
    collected_count: int
    created_count: int = 0
    ready_count: int
    processing_count: int
    status_counts: Dict[str, int] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Ответ с метриками по платформам."""
    platforms: list[PlatformMetric]
    posts_table: dict

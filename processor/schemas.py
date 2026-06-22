"""Pydantic модели для Processor API."""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProcessingOption(BaseModel):
    """Описание одной функции обработки текста."""
    id: str
    name_ru: str
    description: str


class HealthResponse(BaseModel):
    """Ответ healthcheck."""
    status: str
    service: str
    server_time: Optional[str] = None


class CycleResult(BaseModel):
    """Результат одного цикла обработки."""
    status: str
    message: str
    count: int


class LoopStatus(BaseModel):
    """Статус фонового цикла."""
    last_run_at: Optional[datetime] = None
    total_processed: int = 0
    last_cycle_count: int = 0


class ServiceStatus(BaseModel):
    """Полный статус сервиса."""
    service: str
    version: str
    process_interval_sec: int
    process_batch_size: int
    processor: LoopStatus
    current_time: str = ""
    started_at: Optional[str] = None
    processing_options: List[ProcessingOption] = []


class MetricsResponse(BaseModel):
    """Метрики обработки постов."""
    posts_table: Dict[str, Any]

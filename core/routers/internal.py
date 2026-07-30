"""Внутренние эндпоинты для сервисов в Docker-сети (без JWT)."""

from fastapi import APIRouter

from schemas import AiEnabledResponse
from services.system_settings_service import system_settings_service

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/ai-enabled", response_model=AiEnabledResponse)
async def get_ai_enabled() -> AiEnabledResponse:
    """Флаг AI для processor/tg-bot (poll из shared.ai_client)."""
    enabled = await system_settings_service.is_ai_enabled()
    return AiEnabledResponse(enabled=enabled)

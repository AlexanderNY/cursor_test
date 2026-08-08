"""Внутренние эндпоинты для сервисов в Docker-сети (без JWT)."""

from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from schemas import AiEnabledResponse
from services.system_settings_service import system_settings_service
from services.smm_service import smm_service

router = APIRouter(prefix="/internal", tags=["Internal"])


class InboxIngestBody(BaseModel):
    user_id: int
    network: str = Field(..., pattern="^(tg|vk)$")
    external_id: str
    text: str = ""
    author: Optional[str] = None
    external_msg_id: Optional[str] = None
    item_type: str = "comment"
    meta: Optional[dict[str, Any]] = None


@router.get("/ai-enabled", response_model=AiEnabledResponse)
async def get_ai_enabled() -> AiEnabledResponse:
    """Флаг AI для processor/tg-bot (poll из shared.ai_client)."""
    enabled = await system_settings_service.is_ai_enabled()
    return AiEnabledResponse(enabled=enabled)


@router.post("/smm/jobs/run")
async def run_smm_jobs(limit: int = Query(50, ge=1, le=200)):
    """Scheduler/processor drains due smm_publish_jobs."""
    return await smm_service.run_due_jobs(limit)


@router.post("/smm/inbox/ingest")
async def ingest_inbox(body: InboxIngestBody) -> dict[str, Any]:
    """TG/VK collectors push collected messages into unified inbox."""
    item = await smm_service.ingest_from_collector(
        user_id=body.user_id,
        network=body.network,
        external_id=body.external_id,
        text=body.text,
        author=body.author,
        external_msg_id=body.external_msg_id,
        item_type=body.item_type,
        meta=body.meta,
    )
    if not item:
        return {"ok": False, "skipped": True, "reason": "no_collect_channel"}
    return {"ok": True, "item": item}

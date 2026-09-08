"""Внутренние эндпоинты для сервисов в Docker-сети (без JWT)."""

from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from schemas import AiEnabledResponse
from services.system_settings_service import system_settings_service
from services.smm_service import smm_service
from services.platform_auth_service import platform_auth_service

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


class ChannelCounterBumpBody(BaseModel):
    user_id: int
    channel_id: Optional[int] = None
    network: Optional[str] = Field(None, pattern="^(tg|vk)$")
    external_id: Optional[str] = None
    sent: int = 0
    received: int = 0
    failed: int = 0
    alerts_sent: int = 0
    direction: Optional[str] = Field(
        None, pattern="^(collected|published|alert|failed)$"
    )
    platform: Optional[str] = Field(None, pattern="^(tg|vk)$")
    post_id: Optional[int] = None
    external_msg_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class PostMetricSnapshotBody(BaseModel):
    user_id: int
    platform: str = Field(..., pattern="^(tg|vk)$")
    post_id: int
    views: int = 0
    likes: int = 0
    comments: int = 0
    reposts: int = 0


class ChannelSubscriberSnapshotBody(BaseModel):
    channel_id: int
    subscribers: int = 0


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


@router.post("/smm/channel-counter/bump")
async def bump_channel_counter(body: ChannelCounterBumpBody) -> dict[str, Any]:
    ok = await smm_service.bump_channel_from_collector(
        body.user_id,
        channel_id=body.channel_id,
        network=body.network,
        external_id=body.external_id,
        sent=body.sent,
        received=body.received,
        failed=body.failed,
        alerts_sent=body.alerts_sent,
        direction=body.direction,
        platform=body.platform,
        post_id=body.post_id,
        external_msg_id=body.external_msg_id,
        metadata=body.metadata,
    )
    return {"ok": ok}


@router.post("/smm/post-metrics/snapshot")
async def post_metric_snapshot(body: PostMetricSnapshotBody) -> dict[str, Any]:
    await smm_service.record_post_metric_snapshot(
        body.user_id,
        body.platform,
        body.post_id,
        views=body.views,
        likes=body.likes,
        comments=body.comments,
        reposts=body.reposts,
    )
    return {"ok": True}


@router.post("/smm/channel-metrics/subscribers")
async def channel_subscriber_snapshot(body: ChannelSubscriberSnapshotBody) -> dict[str, Any]:
    await smm_service.record_channel_subscriber_snapshot(body.channel_id, body.subscribers)
    return {"ok": True}


class ClaimReadyPostsBody(BaseModel):
    platform: str = Field(
        ...,
        pattern="^(tg|vk|wp|tw|dzen|instagram|threads|url)$",
    )
    limit: int = Field(20, ge=1, le=100)
    user_id: Optional[int] = None


class PublishResultBody(BaseModel):
    platform: str = Field(
        ...,
        pattern="^(tg|vk|wp|tw|dzen|instagram|threads|url)$",
    )
    post_id: int
    ok: bool = True
    external_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/smm/posts/claim")
async def claim_ready_posts(body: ClaimReadyPostsBody) -> dict[str, Any]:
    """Bots claim ready network posts for publish (preferred over direct DB)."""
    posts = await smm_service.claim_ready_posts(
        body.platform, limit=body.limit, user_id=body.user_id
    )
    return {"ok": True, "posts": posts}


@router.post("/smm/posts/publish-result")
async def publish_result(body: PublishResultBody) -> dict[str, Any]:
    """Bots report publish success/failure after claim."""
    ok = await smm_service.apply_publish_result(
        body.platform,
        body.post_id,
        ok=body.ok,
        external_id=body.external_id,
        error=body.error,
    )
    return {"ok": ok}


@router.post("/smm/competitors/sync")
async def sync_competitor_snapshots(user_id: Optional[int] = Query(None)):
    return await smm_service.sync_competitor_snapshots(user_id)


@router.get("/tg/channels/{user_id}")
async def internal_tg_channels(user_id: int) -> dict[str, Any]:
    """Proxy to tg-bot channel list for ownership probes."""
    import httpx
    from config import settings

    base = (settings.TG_BOT_SERVICE_URL or "").rstrip("/")
    if not base:
        return {"ok": False, "channels": []}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base}/tg/channels/{user_id}")
            if resp.status_code >= 400:
                return {"ok": False, "channels": [], "error": resp.text[:200]}
            items = resp.json()
            return {"ok": True, "channels": items if isinstance(items, list) else []}
    except Exception as exc:
        return {"ok": False, "channels": [], "error": str(exc)}


@router.post("/smm/platform/recheck")
async def platform_recheck(user_id: int = Query(..., ge=1)):
    return await platform_auth_service.recheck_user_platform_channels(user_id)


@router.post("/smm/channels/auth/recheck-stale")
async def recheck_stale_channel_auth(max_age_hours: int = Query(24, ge=1, le=168)):
    return await platform_auth_service.recheck_stale_channels(max_age_hours)

"""SMM API: brands, inbox, jobs, automations, analytics, AI."""

from __future__ import annotations

import logging
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from services.smm_service import BRAND_PALETTE, MAX_OWN_CHANNELS, smm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smm", tags=["SMM"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


# ---------- Schemas ----------

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#3B82F6", max_length=7)
    group_id: Optional[int] = None


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=7)
    group_id: Optional[int] = None


class ChannelCreate(BaseModel):
    network: Literal["tg", "vk"]
    external_id: str = Field(..., min_length=1, max_length=128)
    title: Optional[str] = None
    kind: Literal["channel", "group", "public"] = "channel"
    role: Literal["own", "competitor", "source"] = "own"
    color_override: Optional[str] = None


class ChannelUpdate(BaseModel):
    title: Optional[str] = None
    kind: Optional[Literal["channel", "group", "public"]] = None
    role: Optional[Literal["own", "competitor", "source"]] = None
    color_override: Optional[str] = None
    external_id: Optional[str] = None


class JobCreate(BaseModel):
    brand_id: Optional[int] = None
    text: str = Field(..., min_length=1)
    media_urls: List[str] = Field(default_factory=list)
    targets: List[dict[str, Any]] = Field(default_factory=list)
    publish_at: Optional[str] = None
    adapt: bool = True
    status: Optional[str] = None


class JobUpdate(BaseModel):
    source_text: Optional[str] = None
    media: Optional[List[str]] = None
    targets: Optional[List[dict[str, Any]]] = None
    publish_at: Optional[str] = None
    status: Optional[str] = None


class InboxReply(BaseModel):
    text: str = Field(..., min_length=1)


class InboxCreate(BaseModel):
    brand_id: Optional[int] = None
    network: Literal["tg", "vk"]
    channel_id: Optional[int] = None
    thread_id: Optional[str] = None
    type: Literal["dm", "comment", "reaction"]
    author: Optional[str] = None
    text: Optional[str] = None


class AutomationCreate(BaseModel):
    brand_id: int
    type: Literal["rss", "tg_repost", "mention"]
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class AutomationUpdate(BaseModel):
    brand_id: Optional[int] = None
    type: Optional[Literal["rss", "tg_repost", "mention"]] = None
    config: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class AiSummarizeRequest(BaseModel):
    text: str
    max_len: int = 500


class AiRewriteRequest(BaseModel):
    text: str
    tone: Optional[str] = None
    network: Optional[str] = None


class AiAdaptRequest(BaseModel):
    text: str
    targets: List[str] = Field(default_factory=list)


class CompetitorCreate(BaseModel):
    brand_id: int
    network: Literal["tg", "vk"]
    external_id: str
    title: Optional[str] = None
    kind: Literal["channel", "group", "public"] = "channel"


# ---------- Brands ----------

@router.get("/palette")
async def get_palette():
    return {"colors": BRAND_PALETTE, "max_own_channels": MAX_OWN_CHANNELS}


@router.get("/brands")
async def list_brands(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    brands = await smm_service.list_brands(user_id)
    return {"brands": brands}


@router.post("/brands")
async def create_brand(body: BrandCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return await smm_service.create_brand(user_id, body.name, body.color, body.group_id)


@router.get("/brands/{brand_id}")
async def get_brand(brand_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    brand = await smm_service.get_brand(user_id, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.patch("/brands/{brand_id}")
async def update_brand(brand_id: int, body: BrandUpdate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    brand = await smm_service.update_brand(
        user_id, brand_id, name=body.name, color=body.color, group_id=body.group_id
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ok = await smm_service.delete_brand(user_id, brand_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"ok": True}


@router.get("/brands/{brand_id}/channels")
async def list_channels(brand_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    channels = await smm_service.list_channels(user_id, brand_id)
    return {"channels": channels}


@router.post("/brands/{brand_id}/channels")
async def add_channel(brand_id: int, body: ChannelCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.add_channel(
            user_id,
            brand_id,
            network=body.network,
            external_id=body.external_id,
            title=body.title,
            kind=body.kind,
            role=body.role,
            color_override=body.color_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/brands/{brand_id}/channels/{channel_id}")
async def update_channel(
    brand_id: int,
    channel_id: int,
    body: ChannelUpdate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    ch = await smm_service.update_channel(
        user_id,
        brand_id,
        channel_id,
        title=body.title,
        kind=body.kind,
        role=body.role,
        color_override=body.color_override,
        external_id=body.external_id,
    )
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ch


@router.delete("/brands/{brand_id}/channels/{channel_id}")
async def delete_channel(
    brand_id: int, channel_id: int, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    ok = await smm_service.delete_channel(user_id, brand_id, channel_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"ok": True}


# ---------- Inbox ----------

@router.get("/inbox")
async def list_inbox(
    brand_id: Optional[int] = None,
    network: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[int] = None,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return await smm_service.list_inbox(
        user_id, brand_id, network, type, status, limit, cursor
    )


@router.post("/inbox")
async def create_inbox_item(body: InboxCreate, x_user_id: Optional[str] = Header(None)):
    """Internal/collector helper to seed inbox items."""
    user_id = get_user_id(x_user_id)
    return await smm_service.create_inbox_item(user_id, body.model_dump())


@router.post("/inbox/{item_id}/read")
async def mark_read(item_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    item = await smm_service.update_inbox_status(user_id, item_id, "read")
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


@router.post("/inbox/{item_id}/archive")
async def archive_item(item_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    item = await smm_service.update_inbox_status(user_id, item_id, "archived")
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


@router.post("/inbox/{item_id}/reply")
async def reply_item(item_id: int, body: InboxReply, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    item = await smm_service.reply_inbox(user_id, item_id, body.text)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


# ---------- Jobs ----------

@router.post("/jobs")
async def create_job(body: JobCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return await smm_service.create_job(
        user_id=user_id,
        brand_id=body.brand_id,
        text=body.text,
        media=body.media_urls,
        targets=body.targets,
        publish_at=body.publish_at,
        adapt=body.adapt,
        status=body.status or "ready",
    )


@router.get("/jobs")
async def list_jobs(
    brand_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    jobs = await smm_service.list_jobs(user_id, brand_id, date_from, date_to)
    return {"jobs": jobs}


@router.patch("/jobs/{job_id}")
async def update_job(job_id: int, body: JobUpdate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    job = await smm_service.update_job(
        user_id,
        job_id,
        source_text=body.source_text,
        media=body.media,
        targets=body.targets,
        publish_at=body.publish_at,
        status=body.status,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/import-csv")
async def import_csv(
    brand_id: Optional[int] = None,
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("cp1251", errors="replace")
    return await smm_service.import_csv(user_id, brand_id, content)


# ---------- Automations ----------

@router.get("/automations")
async def list_automations(
    brand_id: Optional[int] = None, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    return {"automations": await smm_service.list_automations(user_id, brand_id)}


@router.post("/automations")
async def create_automation(body: AutomationCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.create_automation(
            user_id, body.brand_id, body.type, body.config, body.enabled
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/automations/{automation_id}")
async def update_automation(
    automation_id: int, body: AutomationUpdate, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    item = await smm_service.update_automation(
        user_id,
        automation_id,
        brand_id=body.brand_id,
        type=body.type,
        config=body.config,
        enabled=body.enabled,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Automation not found")
    return item


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ok = await smm_service.delete_automation(user_id, automation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"ok": True}


# ---------- Analytics ----------

@router.get("/analytics/overview")
async def analytics_overview(
    brand_id: Optional[int] = None,
    period: str = "7d",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return await smm_service.analytics_overview(user_id, brand_id, period)


@router.get("/analytics/posts")
async def analytics_posts(
    brand_id: Optional[int] = None,
    sort: str = "er",
    limit: int = Query(20, ge=1, le=100),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return {"posts": await smm_service.analytics_posts(user_id, brand_id, sort, limit)}


@router.get("/analytics/growth")
async def analytics_growth(
    brand_id: Optional[int] = None, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    return await smm_service.analytics_growth(user_id, brand_id)


@router.get("/analytics/best-times")
async def best_times(
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    horizon_days: int = Query(30, ge=7, le=90),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return await smm_service.best_times(user_id, brand_id, channel_id, horizon_days)


# ---------- Competitors ----------

@router.post("/competitors")
async def add_competitor(body: CompetitorCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.add_channel(
            user_id,
            body.brand_id,
            network=body.network,
            external_id=body.external_id,
            title=body.title,
            kind=body.kind,
            role="competitor",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/competitors/{channel_id}/posts")
async def competitor_posts(channel_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return {"posts": await smm_service.competitor_posts(user_id, channel_id)}


# ---------- AI ----------

@router.post("/ai/summarize")
async def ai_summarize(body: AiSummarizeRequest, x_user_id: Optional[str] = Header(None)):
    get_user_id(x_user_id)
    try:
        from shared.ai_client import summarize  # type: ignore

        summary = await summarize(body.text, body.max_len)
        return {"summary": summary}
    except Exception as exc:
        logger.warning("AI summarize fallback: %s", exc)
        truncated = body.text[: body.max_len]
        if len(body.text) > body.max_len:
            truncated += "..."
        return {"summary": truncated, "fallback": True}


@router.post("/ai/rewrite")
async def ai_rewrite(body: AiRewriteRequest, x_user_id: Optional[str] = Header(None)):
    get_user_id(x_user_id)
    try:
        from shared.ai_client import rewrite  # type: ignore

        text = await rewrite(body.text, tone=body.tone, network=body.network)
        return {"text": text}
    except Exception as exc:
        logger.warning("AI rewrite fallback: %s", exc)
        return {"text": body.text, "fallback": True}


@router.post("/ai/adapt")
async def ai_adapt(body: AiAdaptRequest, x_user_id: Optional[str] = Header(None)):
    get_user_id(x_user_id)
    targets = body.targets or ["tg", "vk"]
    variants: dict[str, str] = {}
    try:
        from shared.ai_client import rewrite  # type: ignore

        for net in targets:
            variants[net] = await rewrite(body.text, network=net)
    except Exception as exc:
        logger.warning("AI adapt fallback: %s", exc)
        import re

        plain = re.sub(r"<[^>]+>", "", body.text).strip()
        for net in targets:
            if net == "tg":
                variants[net] = body.text
            else:
                variants[net] = plain
        return {"variants": variants, "fallback": True}
    return {"variants": variants}

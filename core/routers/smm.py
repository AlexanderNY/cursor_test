"""SMM API: brands, inbox, jobs, automations, analytics, AI."""

from __future__ import annotations

import logging
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from services.smm_service import BRAND_PALETTE, compose_brand_voice, smm_service
from services.content_library_service import (
    TEMPLATE_KINDS,
    build_utm_url,
    content_library_service,
)
from services.smm_networks import (
    is_adapt_network,
    network_text_limit,
    normalize_network,
)
from services.quota_service import (
    get_user_tariff,
    get_plan_limits,
    plan_feature,
    ensure_ai_calls_quota,
    ensure_smm_feature,
    get_ai_usage,
    get_usage_summary,
)
from exceptions import QuotaExceededError, ChannelAccessError
from services.platform_auth_service import PlatformAuthError, platform_auth_service, platform_auth_http_detail

SmmNetwork = Literal[
    "tg", "vk", "url", "instagram", "threads", "tw", "dzen", "wp",
    "twitter", "wordpress",  # aliases accepted by API, normalized in service
]
InboxNetwork = Literal[
    "tg", "vk", "url", "instagram", "threads", "tw", "dzen", "wp",
    "twitter", "wordpress",
]
CompetitorNetwork = Literal["tg", "vk", "url"]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smm", tags=["SMM"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


def _http_quota(exc: QuotaExceededError) -> HTTPException:
    if exc.resource == "ai_calls_month":
        message = (
            "Лимит AI-вызовов исчерпан. Обновите план, чтобы продолжить."
            if exc.limit > 0
            else "AI недоступен на текущем плане. Обновите план."
        )
    else:
        message = f"Plan limit exceeded: {exc.resource}"
    return HTTPException(
        status_code=402,
        detail={
            "message": message,
            "resource": exc.resource,
            "limit": exc.limit,
            "used": exc.used,
            "upgrade_url": "/pricing",
        },
    )


def _http_platform_auth(exc: PlatformAuthError) -> HTTPException:
    return HTTPException(status_code=403, detail=platform_auth_http_detail(exc))


# ---------- Schemas ----------

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#3B82F6", max_length=7)
    group_id: Optional[int] = None
    tone_of_voice: Optional[str] = Field(None, max_length=500)
    style_notes: Optional[str] = Field(None, max_length=1000)
    prompt_snippets: Optional[List[dict[str, Any]]] = None


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=7)
    group_id: Optional[int] = None
    tone_of_voice: Optional[str] = Field(None, max_length=500)
    style_notes: Optional[str] = Field(None, max_length=1000)
    prompt_snippets: Optional[List[dict[str, Any]]] = None


class ChannelCreate(BaseModel):
    network: SmmNetwork
    external_id: Optional[str] = Field(None, max_length=128)
    title: Optional[str] = None
    kind: Literal["channel", "group", "public"] = "channel"
    role: Literal["own", "competitor", "source"] = "own"
    color_override: Optional[str] = None
    """Initial page URL for network=url (pre-fills curl_settings / Сбор)."""
    url: Optional[str] = Field(None, max_length=2048)


class ChannelUpdate(BaseModel):
    title: Optional[str] = None
    kind: Optional[Literal["channel", "group", "public"]] = None
    role: Optional[Literal["own", "competitor", "source"]] = None
    color_override: Optional[str] = None
    external_id: Optional[str] = None
    publish_enabled: Optional[bool] = None
    collect_enabled: Optional[bool] = None
    discussion_external_id: Optional[str] = None
    discussion_title: Optional[str] = None
    comments_collect_enabled: Optional[bool] = None
    alert_enabled: Optional[bool] = None
    save_conditions: Optional[List[str]] = None
    conditions_mode: Optional[Literal["any_of", "all_of"]] = None
    processing: Optional[dict[str, Any]] = None
    publish_targets: Optional[List[int]] = None
    alert_delivery: Optional[dict[str, Any]] = None
    alert_rules: Optional[List[dict[str, Any]]] = None
    # Per-URL scrape/processing settings synced into curl_settings.urls[]
    url_config: Optional[dict[str, Any]] = None


class InboxEdit(BaseModel):
    edited_text: str = Field(..., min_length=1)


class InboxRedirect(BaseModel):
    targets: List[dict[str, Any]] = Field(default_factory=list)
    use_edited: bool = True
    publish_at: Optional[str] = None
    pending_approval: bool = False


class InboxCreate(BaseModel):
    brand_id: Optional[int] = None
    network: InboxNetwork
    channel_id: Optional[int] = None
    thread_id: Optional[str] = None
    type: Literal["dm", "comment", "reaction", "competitor_post"]
    author: Optional[str] = None
    text: Optional[str] = None
    external_msg_id: Optional[str] = None
    status: Optional[str] = "new"


class ChannelBind(BaseModel):
    """Bind channel.external_id to a platform profile handle / id."""

    external_id: Optional[str] = Field(None, max_length=128)
    title: Optional[str] = None
    from_profile: bool = False


class InboxReply(BaseModel):
    text: str = Field(..., min_length=1)


class JobCreate(BaseModel):
    brand_id: Optional[int] = None
    text: str = Field(..., min_length=1)
    media_urls: List[str] = Field(default_factory=list)
    targets: List[dict[str, Any]] = Field(default_factory=list)
    publish_at: Optional[str] = None
    adapt: bool = True
    status: Optional[str] = None
    adapter_overrides: Optional[dict[str, Any]] = None
    assigned_to: Optional[int] = None


class JobUpdate(BaseModel):
    source_text: Optional[str] = None
    media: Optional[List[str]] = None
    targets: Optional[List[dict[str, Any]]] = None
    publish_at: Optional[str] = None
    status: Optional[str] = None
    adapters_result: Optional[dict[str, Any]] = None
    assigned_to: Optional[int] = None
    rejection_comment: Optional[str] = None


class JobReject(BaseModel):
    comment: Optional[str] = Field(None, max_length=2000)


class JobAssign(BaseModel):
    assigned_to: Optional[int] = None


class JobBulkApprove(BaseModel):
    job_ids: List[int] = Field(..., min_length=1, max_length=100)


class JobBulkReschedule(BaseModel):
    job_ids: List[int] = Field(..., min_length=1, max_length=100)
    publish_at: str


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
    brand_id: Optional[int] = None


class AiAdaptRequest(BaseModel):
    text: str
    targets: List[str] = Field(default_factory=list)
    brand_id: Optional[int] = None
    tone: Optional[str] = None


class AiProcessRequest(BaseModel):
    action: Literal["summarize", "categorize", "rewrite", "reply_draft"]
    text: str = Field(..., min_length=1, max_length=20000)
    params: Optional[dict[str, Any]] = None
    source: Optional[Literal["inbox", "post"]] = None
    source_id: Optional[int] = None
    brand_id: Optional[int] = None


class CompetitorCreate(BaseModel):
    brand_id: int
    network: CompetitorNetwork
    external_id: Optional[str] = None
    title: Optional[str] = None
    kind: Literal["channel", "group", "public"] = "channel"
    """Page URL for network=url (RSS / Custom URL radar)."""
    url: Optional[str] = Field(None, max_length=2048)
    alert_enabled: bool = False
    sync_interval_min: Optional[int] = Field(None, ge=5, le=1440)


class CompetitorAlertUpdate(BaseModel):
    alert_enabled: Optional[bool] = None
    alert_delivery: Optional[dict[str, Any]] = None
    sync_interval_min: Optional[int] = Field(None, ge=5, le=1440)


class TemplateCreate(BaseModel):
    kind: Literal["prompt", "cta", "utm", "post_body"]
    title: str = Field(..., min_length=1, max_length=255)
    body: str = ""
    metadata: Optional[dict[str, Any]] = None


class TemplateUpdate(BaseModel):
    kind: Optional[Literal["prompt", "cta", "utm", "post_body"]] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    body: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class TemplateApplyRequest(BaseModel):
    job_id: Optional[int] = None
    current_text: Optional[str] = None


class MediaPackCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    object_keys: List[str] = Field(default_factory=list)
    caption: Optional[str] = Field(None, max_length=2000)


class MediaPackUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    object_keys: Optional[List[str]] = None
    caption: Optional[str] = Field(None, max_length=2000)


class MediaPackApplyRequest(BaseModel):
    job_id: Optional[int] = None
    merge: bool = True


class RepublishVariantRequest(BaseModel):
    pending_approval: Optional[bool] = None
    network: Optional[str] = None


class UtmBuildRequest(BaseModel):
    base_url: str = Field(..., min_length=1, max_length=2048)
    params: Optional[dict[str, Any]] = None


# ---------- Brands ----------

@router.get("/palette")
async def get_palette(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    tariff = await get_user_tariff(user_id)
    limits = get_plan_limits(tariff)
    return {
        "colors": BRAND_PALETTE,
        "max_own_channels": limits.get("max_own_channels", 3),
        "tariff": tariff,
        "limits": limits,
    }


@router.get("/plan")
async def get_my_smm_plan(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    tariff = await get_user_tariff(user_id)
    return {"tariff": tariff, "limits": get_plan_limits(tariff)}


@router.get("/usage")
async def get_my_usage_summary(x_user_id: Optional[str] = Header(None)):
    """Used/limit агрегатор для billing и QuotaBanner."""
    user_id = get_user_id(x_user_id)
    return await get_usage_summary(user_id)


@router.get("/channels")
async def list_all_channels(
    brand_id: Optional[int] = None, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    return {"channels": await smm_service.list_all_channels(user_id, brand_id)}


@router.get("/channels/export")
async def export_channels(
    brand_id: Optional[int] = None, x_user_id: Optional[str] = Header(None)
):
    """Download channels as JSON (settings + portable publish/alert target refs)."""
    user_id = get_user_id(x_user_id)
    return await smm_service.export_channels(user_id, brand_id)


class ChannelsImportBody(BaseModel):
    format: Optional[str] = None
    version: Optional[int] = None
    channels: List[dict[str, Any]] = Field(default_factory=list)
    update_existing: bool = True


@router.post("/channels/import")
async def import_channels(
    body: ChannelsImportBody,
    brand_id: int = Query(..., description="Target brand id"),
    x_user_id: Optional[str] = Header(None),
):
    """Import channels into a brand. Matches by network+external_id (URL by page url)."""
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.import_channels(
            user_id,
            brand_id,
            body.model_dump(),
            update_existing=body.update_existing,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/channels/import-file")
async def import_channels_file(
    brand_id: int = Query(...),
    update_existing: bool = Query(True),
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(None),
):
    """Import channels from uploaded JSON file."""
    user_id = get_user_id(x_user_id)
    raw = await file.read()
    try:
        import json as _json

        payload = _json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="JSON root must be an object")
    try:
        return await smm_service.import_channels(
            user_id,
            brand_id,
            payload,
            update_existing=update_existing,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/channels/validate")
async def validate_channels(
    brand_id: int = Query(..., description="Brand to validate"),
    recheck_auth: bool = Query(True, description="Live probe each channel"),
    x_user_id: Optional[str] = Header(None),
):
    """Validate channel access and flow settings for a brand (post-import check)."""
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.validate_brand_channels(
            user_id, brand_id, recheck_auth=recheck_auth
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/brands")
async def list_brands(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    brands = await smm_service.list_brands(user_id)
    return {"brands": brands}


@router.post("/brands")
async def create_brand(body: BrandCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.create_brand(
            user_id,
            body.name,
            body.color,
            body.group_id,
            tone_of_voice=body.tone_of_voice,
            style_notes=body.style_notes,
            prompt_snippets=body.prompt_snippets,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


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
    fields_set = body.model_fields_set if hasattr(body, "model_fields_set") else set()
    brand = await smm_service.update_brand(
        user_id,
        brand_id,
        name=body.name,
        color=body.color,
        group_id=body.group_id,
        tone_of_voice=body.tone_of_voice,
        style_notes=body.style_notes,
        prompt_snippets=body.prompt_snippets,
        clear_tone_of_voice="tone_of_voice" in fields_set and body.tone_of_voice is None,
        clear_style_notes="style_notes" in fields_set and body.style_notes is None,
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
            network=normalize_network(body.network),
            external_id=body.external_id or "",
            title=body.title,
            kind=body.kind,
            role=body.role,
            color_override=body.color_override,
            initial_url=body.url,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ch = await smm_service.get_channel(user_id, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ch


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
        publish_enabled=body.publish_enabled,
        collect_enabled=body.collect_enabled,
        discussion_external_id=body.discussion_external_id,
        discussion_title=body.discussion_title,
        comments_collect_enabled=body.comments_collect_enabled,
        alert_enabled=body.alert_enabled,
        save_conditions=body.save_conditions,
        conditions_mode=body.conditions_mode,
        processing=body.processing,
        publish_targets=body.publish_targets,
        alert_delivery=body.alert_delivery,
        alert_rules=body.alert_rules,
        url_config=body.url_config,
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
    payload = body.model_dump()
    payload["network"] = normalize_network(payload.get("network"))
    return await smm_service.ingest_inbox_item(user_id, payload)


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
    try:
        item = await smm_service.reply_inbox(user_id, item_id, body.text)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


@router.patch("/inbox/{item_id}")
async def edit_inbox_item(item_id: int, body: InboxEdit, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    item = await smm_service.set_inbox_edited_text(user_id, item_id, body.edited_text)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


@router.post("/inbox/{item_id}/redirect")
async def redirect_inbox_item(
    item_id: int, body: InboxRedirect, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.redirect_inbox(
            user_id,
            item_id,
            targets=body.targets,
            use_edited=body.use_edited,
            publish_at=body.publish_at,
            pending_approval=body.pending_approval,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------- Jobs ----------

@router.post("/jobs")
async def create_job(body: JobCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.create_job(
            user_id=user_id,
            brand_id=body.brand_id,
            text=body.text,
            media=body.media_urls,
            targets=body.targets,
            publish_at=body.publish_at,
            adapt=body.adapt,
            status=body.status or "ready",
            adapter_overrides=body.adapter_overrides,
            assigned_to=body.assigned_to,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        job = await smm_service.approve_job(user_id, job_id)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/reject")
async def reject_job(
    job_id: int, body: JobReject, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    try:
        job = await smm_service.reject_job(user_id, job_id, body.comment)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/assign")
async def assign_job(
    job_id: int, body: JobAssign, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    try:
        job = await smm_service.assign_job(user_id, job_id, body.assigned_to)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/bulk-approve")
async def bulk_approve_jobs(body: JobBulkApprove, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.bulk_approve_jobs(user_id, body.job_ids)
    except QuotaExceededError as exc:
        raise _http_quota(exc)


@router.post("/jobs/bulk-reschedule")
async def bulk_reschedule_jobs(
    body: JobBulkReschedule, x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.bulk_reschedule_jobs(
            user_id, body.job_ids, body.publish_at
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)


@router.post("/jobs/run-due")
async def run_due_jobs(
    limit: int = Query(50, ge=1, le=200),
    x_user_id: Optional[str] = Header(None),
):
    """Trigger due job execution (also called by scheduler via internal)."""
    get_user_id(x_user_id)
    return await smm_service.run_due_jobs(limit)


@router.get("/jobs")
async def list_jobs(
    brand_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    status: Optional[str] = None,
    statuses: Optional[str] = Query(
        None, description="Comma-separated statuses, e.g. draft,pending_approval,ready"
    ),
    channel_id: Optional[int] = None,
    network: Optional[str] = None,
    assigned_to: Optional[int] = None,
    assigned_to_me: bool = False,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    status_list = (
        [s.strip() for s in statuses.split(",") if s.strip()] if statuses else None
    )
    jobs = await smm_service.list_jobs(
        user_id,
        brand_id,
        date_from,
        date_to,
        status=status,
        statuses=status_list,
        channel_id=channel_id,
        network=network,
        assigned_to=assigned_to,
        assigned_to_me=assigned_to_me,
    )
    return {"jobs": jobs}


@router.patch("/jobs/{job_id}")
async def update_job(job_id: int, body: JobUpdate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        job = await smm_service.update_job(
            user_id,
            job_id,
            source_text=body.source_text,
            media=body.media,
            targets=body.targets,
            publish_at=body.publish_at,
            status=body.status,
            adapters_result=body.adapters_result,
            assigned_to=body.assigned_to,
            rejection_comment=body.rejection_comment,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/republish-variant")
async def republish_variant(
    job_id: int,
    body: RepublishVariantRequest = RepublishVariantRequest(),
    x_user_id: Optional[str] = Header(None),
):
    """Copy a published/existing job with AI rewrite (brand TOV) into a new draft/approval job."""
    user_id = get_user_id(x_user_id)
    try:
        return await content_library_service.republish_variant(
            user_id,
            job_id,
            pending_approval=body.pending_approval,
            network=body.network,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


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
    try:
        return await smm_service.import_csv(user_id, brand_id, content)
    except QuotaExceededError as exc:
        raise _http_quota(exc)


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
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


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


@router.post("/automations/{automation_id}/run")
async def run_automation(
    automation_id: int,
    limit: int = Query(10, ge=1, le=50),
    x_user_id: Optional[str] = Header(None),
):
    """Pull RSS items into SMM jobs (pending_approval when approval_workflow is on)."""
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.run_automation(user_id, automation_id, limit=limit)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("RSS automation run failed")
        raise HTTPException(status_code=502, detail=f"Feed fetch failed: {exc}") from exc


# ---------- Analytics ----------

@router.get("/analytics/overview")
async def analytics_overview(
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    period: str = "7d",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return await smm_service.analytics_overview(user_id, brand_id, period, channel_id)


@router.get("/analytics/posts")
async def analytics_posts(
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    sort: str = "er",
    limit: int = Query(20, ge=1, le=100),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return {"posts": await smm_service.analytics_posts(user_id, brand_id, sort, limit, channel_id)}


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
    if not plan_feature(await get_user_tariff(user_id), "best_times"):
        raise HTTPException(status_code=402, detail="best_times requires Standard or Full plan")
    return await smm_service.best_times(user_id, brand_id, channel_id, horizon_days)


@router.get("/analytics/channel-stats")
async def channel_stats(
    brand_id: Optional[int] = None,
    period: str = "7d",
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    if not plan_feature(await get_user_tariff(user_id), "channel_stats"):
        raise HTTPException(status_code=402, detail="channel_stats requires an active plan")
    return {
        "channels": await smm_service.channel_stats(user_id, brand_id, period),
        "period": period,
    }


@router.get("/analytics/messages")
async def analytics_messages(
    brand_id: Optional[int] = None,
    period: str = "7d",
    channel_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    return await smm_service.analytics_messages(
        user_id, brand_id, period, channel_id, limit
    )


# ---------- Competitors ----------

@router.get("/competitors")
async def list_competitors(
    brand_id: Optional[int] = None,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        await ensure_smm_feature(user_id, "competitors")
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    return {"competitors": await smm_service.list_competitors(user_id, brand_id)}


@router.post("/competitors")
async def add_competitor(body: CompetitorCreate, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        channel = await smm_service.add_channel(
            user_id,
            body.brand_id,
            network=normalize_network(body.network),
            external_id=body.external_id or "",
            title=body.title,
            kind=body.kind,
            role="competitor",
            initial_url=body.url,
        )
        updates: dict[str, Any] = {}
        if body.alert_enabled:
            updates["alert_enabled"] = True
        if body.sync_interval_min is not None:
            processing = dict(channel.get("processing") or {})
            processing["sync_interval_min"] = body.sync_interval_min
            updates["processing"] = processing
        if updates:
            channel = await smm_service.update_channel(
                user_id, body.brand_id, channel["id"], **updates
            ) or channel
        return channel
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/competitors/compare")
async def competitor_compare(
    brand_id: int = Query(...),
    competitor_channel_id: int = Query(...),
    period: str = Query("7d"),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.competitor_compare(
            user_id, brand_id, competitor_channel_id, period
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.patch("/competitors/{channel_id}")
async def update_competitor_settings(
    channel_id: int,
    body: CompetitorAlertUpdate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        await ensure_smm_feature(user_id, "competitors")
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    ch = await smm_service.get_channel(user_id, channel_id)
    if not ch or ch.get("role") != "competitor":
        raise HTTPException(status_code=404, detail="Competitor not found")
    fields: dict[str, Any] = {}
    if body.alert_enabled is not None:
        fields["alert_enabled"] = body.alert_enabled
    if body.alert_delivery is not None:
        fields["alert_delivery"] = body.alert_delivery
    if body.sync_interval_min is not None:
        processing = dict(ch.get("processing") or {})
        processing["sync_interval_min"] = body.sync_interval_min
        fields["processing"] = processing
    if not fields:
        return ch
    updated = await smm_service.update_channel(
        user_id, int(ch["brand_id"]), channel_id, **fields
    )
    return updated or ch


@router.get("/competitors/{channel_id}/posts")
async def competitor_posts(channel_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return {"posts": await smm_service.competitor_posts(user_id, channel_id)}


@router.get("/competitors/{channel_id}/digest")
async def competitor_digest(
    channel_id: int,
    period: str = Query("24h"),
    with_ai: bool = Query(True),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.competitor_digest(
            user_id, channel_id, period, with_ai=with_ai
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/competitors/{channel_id}/diff")
async def competitor_diff(
    channel_id: int,
    since: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.competitor_diff(user_id, channel_id, since=since)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------- AI ----------

@router.get("/ai/actions")
async def ai_actions(x_user_id: Optional[str] = Header(None)):
    """Каталог безопасных AI-действий (шаблоны, не свободный prompt)."""
    get_user_id(x_user_id)
    from services.ai_assist_service import list_actions

    return {"actions": list_actions()}


@router.get("/ai/usage")
async def ai_usage(x_user_id: Optional[str] = Header(None)):
    """Остаток месячной AI-квоты: {used, limit, period, remaining}."""
    user_id = get_user_id(x_user_id)
    return await get_ai_usage(user_id)


@router.post("/ai/process")
async def ai_process(body: AiProcessRequest, x_user_id: Optional[str] = Header(None)):
    """Шаблонный AI-запрос: action + text + ограниченные params."""
    user_id = get_user_id(x_user_id)
    if not plan_feature(await get_user_tariff(user_id), "ai_composer"):
        raise HTTPException(
            status_code=402,
            detail={
                "message": "AI недоступен на текущем плане. Обновите план.",
                "resource": "feature:ai_composer",
                "upgrade_url": "/pricing",
            },
        )
    try:
        await ensure_ai_calls_quota(user_id)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    from services.ai_assist_service import AiAssistError, process as ai_process_action

    try:
        return await ai_process_action(
            user_id,
            body.action,
            body.text,
            body.params,
            source=body.source,
            source_id=body.source_id,
            brand_id=body.brand_id,
        )
    except AiAssistError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/ai/summarize")
async def ai_summarize(body: AiSummarizeRequest, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    if not plan_feature(await get_user_tariff(user_id), "ai_composer"):
        raise HTTPException(
            status_code=402,
            detail={
                "message": "AI недоступен на текущем плане. Обновите план.",
                "resource": "feature:ai_composer",
                "upgrade_url": "/pricing",
            },
        )
    try:
        await ensure_ai_calls_quota(user_id)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
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
    user_id = get_user_id(x_user_id)
    if not plan_feature(await get_user_tariff(user_id), "ai_composer"):
        raise HTTPException(
            status_code=402,
            detail={
                "message": "AI недоступен на текущем плане. Обновите план.",
                "resource": "feature:ai_composer",
                "upgrade_url": "/pricing",
            },
        )
    try:
        await ensure_ai_calls_quota(user_id)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    tone = body.tone
    if not tone and body.brand_id is not None:
        brand = await smm_service.get_brand(user_id, body.brand_id)
        tone = compose_brand_voice(brand)
    try:
        from shared.ai_client import rewrite  # type: ignore

        text = await rewrite(body.text, tone=tone, network=body.network)
        return {"text": text}
    except Exception as exc:
        logger.warning("AI rewrite fallback: %s", exc)
        return {"text": body.text, "fallback": True}


@router.post("/ai/adapt")
async def ai_adapt(body: AiAdaptRequest, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    if not plan_feature(await get_user_tariff(user_id), "ai_composer"):
        raise HTTPException(
            status_code=402,
            detail={
                "message": "AI недоступен на текущем плане. Обновите план.",
                "resource": "feature:ai_composer",
                "upgrade_url": "/pricing",
            },
        )
    try:
        await ensure_ai_calls_quota(user_id)
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    raw_targets = body.targets or ["tg", "vk"]
    targets: list[str] = []
    seen: set[str] = set()
    for raw in raw_targets:
        net = normalize_network(raw)
        if not is_adapt_network(net) or net in seen:
            continue
        seen.add(net)
        targets.append(net)
    if not targets:
        targets = ["tg", "vk"]

    tone = body.tone
    if not tone and body.brand_id is not None:
        brand = await smm_service.get_brand(user_id, body.brand_id)
        tone = compose_brand_voice(brand)

    variants: dict[str, str] = {}
    limits: dict[str, int] = {}
    try:
        from shared.ai_client import rewrite  # type: ignore

        for net in targets:
            limit = network_text_limit(net) or 4096
            limits[net] = limit
            variants[net] = await rewrite(
                body.text, tone=tone, network=net, max_length=limit
            )
    except Exception as exc:
        logger.warning("AI adapt fallback: %s", exc)
        import re

        plain = re.sub(r"<[^>]+>", "", body.text).strip()
        for net in targets:
            limit = network_text_limit(net) or 4096
            limits[net] = limit
            base = body.text if net == "tg" else plain
            variants[net] = base[:limit] if len(base) > limit else base
        return {"variants": variants, "limits": limits, "fallback": True}
    return {"variants": variants, "limits": limits}


@router.get("/platform-status")
async def platform_status(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return await platform_auth_service.get_all_platform_status(user_id)


@router.get("/channels/{channel_id}/auth")
async def get_channel_auth(channel_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ch = await smm_service.get_channel(user_id, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {
        "channel_id": ch["id"],
        "auth_status": ch.get("auth_status"),
        "auth_error": ch.get("auth_error"),
        "auth_checked_at": ch.get("auth_checked_at"),
        "auth_capabilities": ch.get("auth_capabilities") or {},
    }


@router.get("/channels/{channel_id}/status")
async def get_channel_status(channel_id: int, x_user_id: Optional[str] = Header(None)):
    """Connect status + last collect/publish counters for a channel."""
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.get_channel_connect_status(user_id, channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/channels/{channel_id}/bind")
async def bind_channel(
    channel_id: int,
    body: ChannelBind,
    x_user_id: Optional[str] = Header(None),
):
    """Bind channel.external_id to profile handle (or explicit id) and recheck auth."""
    user_id = get_user_id(x_user_id)
    try:
        return await smm_service.bind_channel_profile(
            user_id,
            channel_id,
            external_id=body.external_id,
            title=body.title,
            from_profile=body.from_profile,
        )
    except PlatformAuthError as exc:
        raise _http_platform_auth(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/channels/{channel_id}/auth/recheck")
async def recheck_channel_auth(channel_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return await platform_auth_service.recheck_channel_auth(user_id, channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ChannelAccessError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/onboarding/state")
async def onboarding_state(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return await platform_auth_service.get_onboarding_state(user_id)


@router.post("/onboarding/skip")
async def onboarding_skip(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return await platform_auth_service.set_onboarding_skipped(user_id, True)


@router.post("/onboarding/seed-demo")
async def onboarding_seed_demo(
    x_user_id: Optional[str] = Header(None),
    force: bool = False,
):
    """One-click учебный демо-бренд (S01). Без UTM — передайте force=true."""
    user_id = get_user_id(x_user_id)
    return await platform_auth_service.seed_demo_onboarding(user_id, force=force)


# ---------- Content library ----------

@router.get("/brands/{brand_id}/templates")
async def list_templates(
    brand_id: int,
    kind: Optional[str] = None,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    if kind and kind not in TEMPLATE_KINDS:
        raise HTTPException(status_code=422, detail=f"Invalid kind: {kind}")
    try:
        templates = await content_library_service.list_templates(user_id, brand_id, kind)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"templates": templates}


@router.post("/brands/{brand_id}/templates")
async def create_template(
    brand_id: int,
    body: TemplateCreate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await content_library_service.create_template(
            user_id,
            brand_id,
            kind=body.kind,
            title=body.title,
            body=body.body,
            metadata=body.metadata,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: int,
    body: TemplateUpdate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        tpl = await content_library_service.update_template(
            user_id,
            template_id,
            title=body.title,
            body=body.body,
            metadata=body.metadata,
            kind=body.kind,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ok = await content_library_service.delete_template(user_id, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: int,
    body: TemplateApplyRequest = TemplateApplyRequest(),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await content_library_service.apply_template(
            user_id,
            template_id,
            job_id=body.job_id,
            current_text=body.current_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/brands/{brand_id}/media-packs")
async def list_media_packs(brand_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        packs = await content_library_service.list_media_packs(user_id, brand_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"media_packs": packs}


@router.post("/brands/{brand_id}/media-packs")
async def create_media_pack(
    brand_id: int,
    body: MediaPackCreate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await content_library_service.create_media_pack(
            user_id,
            brand_id,
            title=body.title,
            object_keys=body.object_keys,
            caption=body.caption,
        )
    except QuotaExceededError as exc:
        raise _http_quota(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.patch("/media-packs/{pack_id}")
async def update_media_pack(
    pack_id: int,
    body: MediaPackUpdate,
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    clear_caption = body.caption is not None and body.caption.strip() == ""
    try:
        pack = await content_library_service.update_media_pack(
            user_id,
            pack_id,
            title=body.title,
            object_keys=body.object_keys,
            caption=body.caption,
            clear_caption=clear_caption,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not pack:
        raise HTTPException(status_code=404, detail="Media pack not found")
    return pack


@router.delete("/media-packs/{pack_id}")
async def delete_media_pack(pack_id: int, x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    ok = await content_library_service.delete_media_pack(user_id, pack_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Media pack not found")
    return {"ok": True}


@router.post("/media-packs/{pack_id}/apply")
async def apply_media_pack(
    pack_id: int,
    body: MediaPackApplyRequest = MediaPackApplyRequest(),
    x_user_id: Optional[str] = Header(None),
):
    user_id = get_user_id(x_user_id)
    try:
        return await content_library_service.apply_media_pack(
            user_id,
            pack_id,
            job_id=body.job_id,
            merge=body.merge,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/library/utm/build")
async def build_utm_link(body: UtmBuildRequest, x_user_id: Optional[str] = Header(None)):
    get_user_id(x_user_id)
    url = build_utm_url(body.base_url, body.params)
    return {"url": url}


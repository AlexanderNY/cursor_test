"""Learn API for 9to18.ru — public read + site_admin write (db_9to18)."""
from __future__ import annotations

import json
from typing import Any, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr, Field

from database import get_db_connection, release_db_connection
from services.learn_article_md import load_article_template, parse_learn_article_md
from services.learn_service import VALID_RUBRICS, learn_service

# Reuse site JWT helpers (site_admin only for CMS)
from routers import site as site_router

router = APIRouter(prefix="/learn", tags=["Learn"])

SITE_PROMO_KEY = "site_9to18_promo"

DEFAULT_SITE_PROMO: dict[str, Any] = {
    "enabled": True,
    "serviceSlug": "copyparse",
    "eyebrow": "Спотлайт · взаимное продвижение",
    "title": "CopyParse: SaaS кросспостинга как живой стенд",
    "body": (
        "9to18 — площадка взаимного продвижения проектов. "
        "Сейчас в фокусе CopyParse: бренды, каналы, календарь и inbox."
    ),
    "ctaLabel": "Открыть copyparse.ru",
    "ctaHref": "https://www.copyparse.ru",
}


class LearnLinkIn(BaseModel):
    label: str = ""
    href: str = ""


class LearnPostIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    episode: str = ""
    title: str = Field(..., min_length=1, max_length=512)
    shortTitle: str = ""
    rubricId: str = "architecture"
    order: int = 0
    theory: str = ""
    lab: str = ""
    cheatsheet: str = ""
    diagram: str = ""
    links: List[LearnLinkIn] = Field(default_factory=list)
    structured: Optional[dict[str, Any]] = None
    theoryFormat: str = "markdown"
    labFormat: str = "markdown"
    cheatsheetFormat: str = "markdown"
    profiles: List[str] = Field(default_factory=list)
    level: str = ""
    tags: List[str] = Field(default_factory=list)
    excerpt: str = ""
    durationMin: int = 0
    prerequisites: List[str] = Field(default_factory=list)
    author: str = ""
    authorUrl: str = ""
    coverUrl: str = ""
    seoTitle: str = ""
    seoDescription: str = ""
    seoKeywords: List[str] = Field(default_factory=list)
    canonicalUrl: str = ""
    publishedAt: str


class LearnImportIn(BaseModel):
    markdown: str = Field(..., min_length=1)
    save: bool = False


class LearnScheduleIn(BaseModel):
    startIso: str
    intervalDays: float = 1


class LearnContactIn(BaseModel):
    name: str = Field(default="", max_length=120)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=4000)


class LearnPromoIn(BaseModel):
    enabled: bool = True
    serviceSlug: str = Field(default="copyparse", max_length=64)
    eyebrow: str = Field(default="", max_length=120)
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=4000)
    ctaLabel: str = Field(default="Подробнее", max_length=80)
    ctaHref: str = Field(default="/", max_length=500)


def _normalize_promo(raw: Any) -> dict[str, Any]:
    data = DEFAULT_SITE_PROMO.copy()
    if isinstance(raw, dict):
        for key in (
            "enabled",
            "serviceSlug",
            "eyebrow",
            "title",
            "body",
            "ctaLabel",
            "ctaHref",
        ):
            if key in raw and raw[key] is not None:
                data[key] = raw[key]
    data["enabled"] = bool(data.get("enabled", True))
    data["serviceSlug"] = str(data.get("serviceSlug") or "copyparse")[:64]
    data["eyebrow"] = str(data.get("eyebrow") or "")[:120]
    data["title"] = str(data.get("title") or DEFAULT_SITE_PROMO["title"])[:200]
    data["body"] = str(data.get("body") or DEFAULT_SITE_PROMO["body"])[:4000]
    data["ctaLabel"] = str(data.get("ctaLabel") or "Подробнее")[:80]
    data["ctaHref"] = str(data.get("ctaHref") or "/")[:500]
    return data


async def _require_site_admin(authorization: Optional[str]) -> dict[str, Any]:
    user = await site_router._require_user(authorization)
    site_router._require_super_admin(user)
    return user


def _is_site_admin_token(authorization: Optional[str]) -> bool:
    try:
        token = site_router._bearer_token(authorization)
        if not token:
            return False
        payload = site_router._decode_site_token(token)
        return str(payload.get("site_role") or "") == "site_admin"
    except Exception:
        return False


async def _get_setting(key: str, default: Any) -> Any:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT value FROM site_settings WHERE key = %s",
                (key,),
            )
            row = await cur.fetchone()
            if not row:
                return default
            value = row[0]
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            return value if value is not None else default
    finally:
        await release_db_connection(conn)


async def _set_setting(key: str, value: Any) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_settings (key, value, updated_at)
                VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value, ensure_ascii=False)),
            )
    finally:
        await release_db_connection(conn)


@router.get("/posts")
async def list_learn_posts(
    preview: bool = Query(False),
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    include = bool(preview and _is_site_admin_token(authorization))
    posts = await learn_service.list_posts(include_unpublished=include)
    return {"posts": posts}


@router.get("/posts/{slug}")
async def get_learn_post(
    slug: str,
    preview: bool = Query(False),
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    include = bool(preview and _is_site_admin_token(authorization))
    post = await learn_service.get_post(slug, include_unpublished=include)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/promo")
async def get_site_promo() -> dict[str, Any]:
    raw = await _get_setting(SITE_PROMO_KEY, DEFAULT_SITE_PROMO)
    return _normalize_promo(raw)


@router.put("/admin/promo")
async def put_site_promo(
    body: LearnPromoIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    payload = _normalize_promo(body.model_dump())
    await _set_setting(SITE_PROMO_KEY, payload)
    return payload


@router.get("/admin/posts")
async def admin_list_posts(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    posts = await learn_service.list_posts(include_unpublished=True)
    return {"posts": posts}


@router.get("/admin/article-template")
async def admin_article_template(
    authorization: Optional[str] = Header(None),
) -> PlainTextResponse:
    await _require_site_admin(authorization)
    return PlainTextResponse(
        content=load_article_template(),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="learn-article-template.md"'
        },
    )


@router.post("/admin/posts/import")
async def admin_import_post(
    body: LearnImportIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    try:
        payload, warnings = parse_learn_article_md(body.markdown)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not payload.get("slug") or not payload.get("title"):
        raise HTTPException(
            status_code=422,
            detail="В frontmatter нужны slug и title",
        )
    if payload.get("rubricId") not in VALID_RUBRICS:
        raise HTTPException(status_code=422, detail="Invalid rubricId")
    saved = False
    post: dict[str, Any] = payload
    if body.save:
        try:
            post = await learn_service.upsert_post(payload)
            saved = True
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"post": post, "warnings": warnings, "saved": saved}


@router.post("/admin/posts")
async def admin_upsert_post(
    body: LearnPostIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    if body.rubricId not in VALID_RUBRICS:
        raise HTTPException(status_code=422, detail="Invalid rubricId")
    try:
        return await learn_service.upsert_post(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/admin/posts/{slug}")
async def admin_patch_post(
    slug: str,
    body: LearnPostIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    payload = body.model_dump()
    payload["slug"] = slug
    try:
        return await learn_service.upsert_post(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/admin/posts/{slug}")
async def admin_delete_post(
    slug: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    ok = await learn_service.delete_post(slug)
    if not ok:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True, "slug": slug}


@router.post("/admin/reset-to-seed")
async def admin_reset_to_seed(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    try:
        inserted = await learn_service.reset_to_seed()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    posts = await learn_service.list_posts(include_unpublished=True)
    return {"inserted": inserted, "posts": posts}


@router.post("/admin/schedule")
async def admin_schedule(
    body: LearnScheduleIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await _require_site_admin(authorization)
    try:
        posts = await learn_service.schedule_all(body.startIso, body.intervalDays)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"posts": posts}


@router.post("/contact")
async def submit_contact(body: LearnContactIn) -> dict[str, Any]:
    """Публичная обратная связь → site_contacts."""
    name = body.name.strip()
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_contacts (app_slug, name, email, message, status)
                VALUES (%s, %s, %s, %s, 'new')
                RETURNING id, created_at
                """,
                ("learn", name, str(body.email), message),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Не удалось сохранить сообщение")
            return {
                "id": row[0],
                "created_at": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
                "ok": True,
            }
    finally:
        await release_db_connection(conn)

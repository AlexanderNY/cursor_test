"""Learn API for 9to18.ru (public read + admin/author write + progress)."""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from database import get_db_connection, release_db_connection
from services.learn_service import VALID_RUBRICS, learn_service
from services.system_settings_service import system_settings_service

router = APIRouter(prefix="/learn", tags=["Learn"])

SITE_PROMO_KEY = "site_9to18_promo"

DEFAULT_SITE_PROMO: dict[str, Any] = {
    "enabled": True,
    "serviceSlug": "copyparse",
    "eyebrow": "Спотлайт · взаимное продвижение",
    "title": "CopyParse: SaaS кросспостинга как живой стенд",
    "body": (
        "9to18 — площадка взаимного продвижения проектов. "
        "Сейчас в фокусе CopyParse: бренды, каналы, календарь и inbox — "
        "тот же стек, который разбираем в Learn. Поддержите развитие сервиса "
        "и загляните на стенд."
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
    theoryFormat: str = "markdown"
    labFormat: str = "markdown"
    cheatsheetFormat: str = "markdown"
    publishedAt: str


class LearnScheduleIn(BaseModel):
    startIso: str
    intervalDays: float = 1


class LearnProgressIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    completed: bool = True


class LearnContactIn(BaseModel):
    """Публичная форма обратной связи 9to18.ru."""

    name: str = Field(default="", max_length=120)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=4000)


class LearnPromoIn(BaseModel):
    """Рекламный спотлайт на главной 9to18.ru (один пост)."""

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


def _require_editor(x_user_id: Optional[str], x_user_role: Optional[str]) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authorization required")
    role = (x_user_role or "").strip().lower()
    if role not in ("admin", "author"):
        raise HTTPException(
            status_code=403,
            detail="Only admin or author can manage Learn posts",
        )
    try:
        return int(x_user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid user id") from exc


def _optional_user_id(x_user_id: Optional[str]) -> Optional[int]:
    if not x_user_id:
        return None
    try:
        return int(x_user_id)
    except (TypeError, ValueError):
        return None


def _can_preview(x_user_role: Optional[str]) -> bool:
    return (x_user_role or "").strip().lower() in ("admin", "author")


@router.get("/posts")
async def list_learn_posts(
    preview: bool = Query(False),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    include = bool(preview and _can_preview(x_user_role))
    posts = await learn_service.list_posts(include_unpublished=include)
    return {"posts": posts}


@router.get("/posts/{slug}")
async def get_learn_post(
    slug: str,
    preview: bool = Query(False),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    include = bool(preview and _can_preview(x_user_role))
    post = await learn_service.get_post(slug, include_unpublished=include)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/promo")
async def get_site_promo() -> dict[str, Any]:
    """Публичный рекламный пост для главной 9to18.ru."""
    raw = await system_settings_service.get_value(SITE_PROMO_KEY, DEFAULT_SITE_PROMO)
    return _normalize_promo(raw)


@router.put("/admin/promo")
async def put_site_promo(
    body: LearnPromoIn,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    """Редактирование спотлайта главной (admin/author)."""
    _require_editor(x_user_id, x_user_role)
    payload = _normalize_promo(body.model_dump())
    await system_settings_service.set_value(SITE_PROMO_KEY, payload)
    return payload


@router.get("/admin/posts")
async def admin_list_posts(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
    posts = await learn_service.list_posts(include_unpublished=True)
    return {"posts": posts}


@router.post("/admin/posts")
async def admin_upsert_post(
    body: LearnPostIn,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
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
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
    payload = body.model_dump()
    payload["slug"] = slug
    try:
        return await learn_service.upsert_post(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/admin/posts/{slug}")
async def admin_delete_post(
    slug: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
    ok = await learn_service.delete_post(slug)
    if not ok:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True, "slug": slug}


@router.post("/admin/reset-to-seed")
async def admin_reset_to_seed(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
    try:
        inserted = await learn_service.reset_to_seed()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    posts = await learn_service.list_posts(include_unpublished=True)
    return {"inserted": inserted, "posts": posts}


@router.post("/admin/schedule")
async def admin_schedule(
    body: LearnScheduleIn,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_editor(x_user_id, x_user_role)
    try:
        posts = await learn_service.schedule_all(body.startIso, body.intervalDays)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"posts": posts}


@router.post("/contact")
async def submit_contact(body: LearnContactIn) -> dict[str, Any]:
    """Публичная обратная связь с 9to18 → таблица feedback (без JWT)."""
    name = body.name.strip()
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    text_parts = ["[9to18]"]
    if name:
        text_parts.append(f"Имя: {name}")
    text_parts.append(message)
    text = "\n".join(text_parts)

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO feedback (type, text, email, user_id)
                VALUES (%s, %s, %s, NULL)
                RETURNING id, created_at
                """,
                ("contact_author", text, str(body.email)),
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


@router.get("/progress")
async def get_progress(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> dict[str, Any]:
    user_id = _optional_user_id(x_user_id)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    items = await learn_service.list_progress(user_id)
    return {"items": items}


@router.put("/progress")
async def put_progress(
    body: LearnProgressIn,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> dict[str, Any]:
    user_id = _optional_user_id(x_user_id)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        return await learn_service.set_progress(
            user_id, body.slug, completed=body.completed
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

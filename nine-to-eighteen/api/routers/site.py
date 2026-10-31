"""9to18.ru site contour: auth, apps, blogs, contacts.

Роли:
- user — сервисы витрины и статьи блогов
- админ сервиса (site_app_admins) — плашка и отдельный блог своих сервисов
- супер-админ (site_users.site_role = site_admin) — всё выше + любой сервис,
  спотлайт, назначение админов сервисов
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets as py_secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import bcrypt
import jwt
from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field

from config import settings
from database import get_site_db_connection, release_site_db_connection
from rate_limit import enforce_rate_limit
from upload_limits import read_upload_limited
import async_fs
from services.cert_rules import (
    CERT_QUIZ_PERCENT,
    INTERVIEW_CERT_PERCENT,
    INTERVIEW_TRACK_ID,
    assess_interview_track,
    assess_tracks,
    best_quiz_percents,
    blank_code,
    certificate_holder_name,
    is_cert_code,
)
from services.photo_process import process_profile_photo
from storage_client import get_storage

UPLOADS_SITE_RESUME_DIR = Path("uploads/site/resume")
UPLOADS_SITE_NOTES_DIR = Path("uploads/site/notes")
S3_SITE_RESUME_PREFIX = "site/resume"
S3_SITE_NOTES_PREFIX = "site/notes"
ALLOWED_RESUME_PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_NOTE_FILE_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
    ".txt",
    ".md",
}
NOTE_MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
}
MAX_NOTE_FILE_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/site", tags=["Site9to18"])

SITE_AUD = "9to18"
SITE_PROMO_KEY = "site_9to18_promo"
SITE_LEARNING_MAP_KEY = "site_9to18_learning_map"
LEARNING_MAP_MAX_CHARS = 1_500_000
ACCESS_MINUTES = 60 * 12
ALGORITHM = "HS256"

# Live home tiles only. Legacy stub slugs are hidden by _ensure_featured_apps.
DEFAULT_APPS: list[dict[str, Any]] = [
    {
        "slug": "bowl",
        "title": "Bowl",
        "subtitle": "Игра · перки · заказы",
        "description": "2D-игра на Python в браузере: выживание в чаше, перки, боссы и заказы между матчами.",
        "accent": "#34d399",
        "emoji": "🎳",
        "app_path": "/game/bowl",
        "sort_order": 1,
    },
    {
        "slug": "learn",
        "title": "Learn",
        "subtitle": "Статьи · Anki · лабы",
        "description": "Единый формат учебных статей: теория, схемы, тест, Anki; лаба опционально.",
        "accent": "#2dd4bf",
        "emoji": "📚",
        "app_path": "/game/learn",
        "sort_order": 2,
    },
    {
        "slug": "learning-map",
        "title": "Карта обучения",
        "subtitle": "Профили · статьи Learn",
        "description": (
            "Mind map к собеседованию: профили (аналитик, DevOps, разработчик, QA, PO). "
            "Каждый лист — статья Learn с Anki."
        ),
        "accent": "#2dd4bf",
        "emoji": "🗺️",
        "app_path": "/game/learning-map",
        "sort_order": 3,
    },
    {
        "slug": "hh-resume",
        "title": "Резюме",
        "subtitle": "Опросник · HH · навыки Learn",
        "description": (
            "Отдельный сервис: опросник «идеальное резюме», шаблон в стиле HeadHunter, "
            "правка текста и навыки из пройденных выпусков Learn."
        ),
        "accent": "#d6001c",
        "emoji": "📄",
        "app_path": "/game/hh-resume",
        "sort_order": 4,
    },
    {
        "slug": "portfolio",
        "title": "Портфолио",
        "subtitle": "Кейсы · публичная страница",
        "description": (
            "Публичная страница кейсов: задача, что сделано, результат, стек, "
            "выпуски Learn и сертификат сезона."
        ),
        "accent": "#38bdf8",
        "emoji": "🗂️",
        "app_path": "/game/portfolio",
        "sort_order": 5,
    },
    {
        "slug": "trainers",
        "title": "Тренажёры",
        "subtitle": "Code · SQL · Git",
        "description": (
            "Песочницы в браузере: Python (Pyodide), SQL (SQLite) и симулятор Git. "
            "У каждого — свободный режим и каталог задач из Learn."
        ),
        "accent": "#2dd4bf",
        "emoji": "⌨️",
        "app_path": "/game/code",
        "sort_order": 6,
    },
    {
        "slug": "copyparse",
        "title": "CopyParse",
        "subtitle": "SaaS · copyparse.ru",
        "description": "Платформа кросспостинга и SMM — живой стенд курса.",
        "accent": "#fb923c",
        "emoji": "🚀",
        "external_href": "https://www.copyparse.ru",
        "sort_order": 9,
    },
    {
        "slug": "mnemonics",
        "title": "Мнемотехники",
        "subtitle": "Акронимы · цепочки · крючки",
        "description": (
            "Тренажёр кодирования для собеса: акронимы, акростихи, чанкинг, "
            "цепочки и система крючков. Дриллы из статей Learn и с карты знаний."
        ),
        "accent": "#a78bfa",
        "emoji": "🧩",
        "app_path": "/game/mnemonics",
        "sort_order": 10,
    },
]

DEFAULT_PROMO: dict[str, Any] = {
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
    # Пустой список = авто (последние опубликованные). Иначе ручной выбор ключей "appSlug/postSlug".
    "curatedKeys": [],
}


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class LoginIn(BaseModel):
    login: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class AppUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=128)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    accent: Optional[str] = Field(default=None, max_length=32)
    emoji: Optional[str] = Field(default=None, max_length=16)
    external_href: Optional[str] = Field(default=None, max_length=512)
    app_path: Optional[str] = Field(default=None, max_length=255)
    is_visible: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=10000)


class AppCreateIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(..., min_length=1, max_length=128)
    subtitle: str = Field(default="", max_length=255)
    description: str = Field(default="")
    accent: str = Field(default="#2dd4bf", max_length=32)
    emoji: str = Field(default="", max_length=16)
    external_href: str = Field(default="", max_length=512)
    app_path: str = Field(default="", max_length=255)
    is_visible: bool = True
    sort_order: Optional[int] = Field(default=None, ge=0, le=10000)


class AppsReorderIn(BaseModel):
    slugs: list[str] = Field(..., min_length=1)


class PostIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=512)
    body: str = Field(default="", max_length=120000)
    is_published: bool = True


class ContactIn(BaseModel):
    name: str = Field(default="", max_length=120)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=4000)
    app_slug: str = Field(default="", max_length=64)


class PromoIn(BaseModel):
    enabled: bool = True
    eyebrow: str = Field(default="Спотлайт · взаимное продвижение", max_length=120)
    # Ручной выбор карточек: ["learn/about", "bowl/about"] — пусто = авто по дате
    curatedKeys: list[str] = Field(default_factory=list, max_length=5)
    # legacy fields (игнорируются каруселью, хранятся для совместимости)
    serviceSlug: str = Field(default="copyparse", max_length=64)
    title: str = Field(default="", max_length=200)
    body: str = Field(default="", max_length=4000)
    ctaLabel: str = Field(default="Подробнее", max_length=80)
    ctaHref: str = Field(default="/", max_length=500)


class LearningMapIn(BaseModel):
    markdown: str = Field(..., min_length=1, max_length=LEARNING_MAP_MAX_CHARS)


class AssignAdminIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    app_slug: str = Field(..., min_length=1, max_length=64)


class ContactStatusIn(BaseModel):
    status: str = Field(..., pattern=r"^(new|read|done)$")


class UserPatchIn(BaseModel):
    site_role: Optional[str] = Field(default=None, pattern=r"^(user|site_admin)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    """Полный список slug сервисов, где пользователь — админ (заменяет текущий)."""
    app_admin: Optional[list[str]] = None


class UnassignAdminIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    app_slug: str = Field(..., min_length=1, max_length=64)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordForgotIn(BaseModel):
    login: str = Field(..., min_length=1, max_length=255)


class PasswordResetIn(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class LearnProgressIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    completed: bool = True


class ChecklistItemIn(BaseModel):
    id: str = Field(default="", max_length=64)
    title: str = Field(..., min_length=1, max_length=256)
    done: bool = False


class UserTaskCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    notes: str = Field(default="", max_length=8000)
    tag: str = Field(default="", max_length=64)
    due_at: Optional[str] = Field(default=None, max_length=32)
    due_time: Optional[str] = Field(default=None, max_length=16)
    remind_at: Optional[str] = Field(default=None, max_length=64)
    priority: str = Field(default="normal", max_length=16)
    board: str = Field(default="backlog", max_length=16)
    checklist: list[ChecklistItemIn] = Field(default_factory=list)
    repeat_rule: str = Field(default="none", max_length=16)
    parent_id: Optional[int] = None


class UserTaskUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=512)
    notes: Optional[str] = Field(default=None, max_length=8000)
    tag: Optional[str] = Field(default=None, max_length=64)
    # None = no change; "" = clear due date; "YYYY-MM-DD" = set
    due_at: Optional[str] = Field(default=None, max_length=32)
    due_time: Optional[str] = Field(default=None, max_length=16)
    remind_at: Optional[str] = Field(default=None, max_length=64)
    priority: Optional[str] = Field(default=None, max_length=16)
    board: Optional[str] = Field(default=None, max_length=16)
    checklist: Optional[list[ChecklistItemIn]] = None
    repeat_rule: Optional[str] = Field(default=None, max_length=16)
    parent_id: Optional[int] = None
    completed: Optional[bool] = None
    sort_order: Optional[int] = None


class HabitCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    tag: str = Field(default="", max_length=64)
    color: str = Field(default="", max_length=32)


class HabitUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    tag: Optional[str] = Field(default=None, max_length=64)
    color: Optional[str] = Field(default=None, max_length=32)
    is_archived: Optional[bool] = None
    sort_order: Optional[int] = None


class HabitCheckIn(BaseModel):
    day: Optional[str] = Field(default=None, max_length=32)
    checked: bool = True


class NoteCreateIn(BaseModel):
    title: str = Field(default="", max_length=512)
    body: str = Field(default="", max_length=100_000)
    tag: str = Field(default="", max_length=64)


class NoteUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)
    body: Optional[str] = Field(default=None, max_length=100_000)
    tag: Optional[str] = Field(default=None, max_length=64)


class FocusLogCreateIn(BaseModel):
    minutes: int = Field(..., ge=1, le=180)
    label: str = Field(default="", max_length=128)


class QuizAttemptIn(BaseModel):
    source_type: str = Field(default="post", pattern=r"^(post|learn|quiz_page)$")
    source_key: str = Field(..., min_length=1, max_length=255)
    score: int = Field(..., ge=0, le=500)
    total: int = Field(..., ge=0, le=500)
    answers: list[Any] = Field(default_factory=list)


class AnkiReviewIn(BaseModel):
    card_id: str = Field(..., min_length=1, max_length=255)
    front: str = Field(default="", max_length=2000)
    back: str = Field(default="", max_length=8000)
    source_key: str = Field(default="", max_length=255)
    ease: int = Field(..., ge=1, le=4)  # 1 again, 2 hard, 3 good, 4 easy


class ProfileUpdateIn(BaseModel):
    last_name: Optional[str] = Field(default=None, max_length=120)
    first_name: Optional[str] = Field(default=None, max_length=120)
    patronymic: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=64)
    birth_date: Optional[str] = Field(default=None, max_length=32)
    city: Optional[str] = Field(default=None, max_length=120)
    citizenship: Optional[str] = Field(default=None, max_length=120)
    ready_for_trips: Optional[bool] = None



def _secret() -> str:
    secret = (settings.JWT_SECRET_KEY or "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET_KEY is not configured")
    return secret


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_access_token(
    *,
    user_id: int,
    site_role: str,
    app_admin: list[str],
    username: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "username": username,
        "site_role": site_role,
        "app_admin": app_admin,
        "type": "site_access",
        "aud": SITE_AUD,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_MINUTES),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _decode_site_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            audience=SITE_AUD,
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if payload.get("type") != "site_access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


async def _app_admin_slugs(user_id: int) -> list[str]:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT app_slug FROM site_app_admins WHERE user_id = %s ORDER BY app_slug",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [str(row[0]) for row in rows]
    finally:
        await release_site_db_connection(conn)


async def _require_user(authorization: Optional[str]) -> dict[str, Any]:
    """JWT только идентифицирует user_id; роль и активность всегда из БД."""
    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = _decode_site_token(token)
    user_id = int(payload["user_id"])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT username, site_role, is_active, email
                FROM site_users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    if not bool(row[2]):
        raise HTTPException(status_code=403, detail="Account disabled")
    app_admin = await _app_admin_slugs(user_id)
    return {
        "user_id": user_id,
        "username": str(row[0] or ""),
        "site_role": str(row[1] or "user"),
        "email": str(row[3] or ""),
        "app_admin": app_admin,
    }


def _is_super_admin(user: dict[str, Any]) -> bool:
    """Супер-админ сайта (site_role=site_admin): любой сервис, спотлайт, назначения."""
    return str(user.get("site_role") or "") == "site_admin"


def _can_manage_app(user: dict[str, Any], app_slug: str) -> bool:
    """Супер-админ или админ конкретного сервиса (site_app_admins)."""
    if _is_super_admin(user):
        return True
    return app_slug in (user.get("app_admin") or [])


def _require_super_admin(user: dict[str, Any]) -> None:
    if not _is_super_admin(user):
        raise HTTPException(status_code=403, detail="Требуется роль супер-админа")

def _row_app(row: tuple) -> dict[str, Any]:
    return {
        "slug": row[0],
        "title": row[1],
        "subtitle": row[2] or "",
        "description": row[3] or "",
        "accent": row[4] or "#2dd4bf",
        "emoji": row[5] or "",
        "externalHref": row[6] or "",
        "appPath": row[7] or "",
        "isVisible": bool(row[8]),
        "sortOrder": int(row[9] or 0),
        "updatedAt": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
    }


def _row_post(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "appSlug": row[1],
        "slug": row[2],
        "title": row[3],
        "body": row[4] or "",
        "isPublished": bool(row[5]),
        "publishedAt": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
        "updatedAt": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
    }


async def ensure_site_seeded() -> None:
    """Idempotent bootstrap of featured apps. Call only from app lifespan."""
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'site_apps'
                )
                """
            )
            exists_row = await cur.fetchone()
            if not exists_row or not exists_row[0]:
                return
            await cur.execute("SELECT COUNT(*) FROM site_apps")
            count_row = await cur.fetchone()
            if not count_row or int(count_row[0] or 0) == 0:
                for app in DEFAULT_APPS:
                    await cur.execute(
                        """
                        INSERT INTO site_apps (
                            slug, title, subtitle, description, accent, emoji,
                            external_href, app_path, is_visible, sort_order
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                        ON CONFLICT (slug) DO NOTHING
                        """,
                        (
                            app["slug"],
                            app["title"],
                            app.get("subtitle", ""),
                            app.get("description", ""),
                            app.get("accent", "#2dd4bf"),
                            app.get("emoji", ""),
                            app.get("external_href", ""),
                            app.get("app_path", ""),
                            int(app.get("sort_order") or 0),
                        ),
                    )
            await _ensure_featured_apps(cur)
    finally:
        await release_site_db_connection(conn)


async def _ensure_featured_apps(cur: Any) -> None:
    """Insert missing featured tiles. Never overwrite admin content."""
    stub_hide_slugs = {
        "e2e-tester",
        "menu",
        "rating",
        "events",
        "help",
        "chat",
        "stream",
        "news",
        "forum",
        "map",
        "team",
        # Кабинет и срезы Learn, не отдельные сервисы витрины.
        "profile",
        "tasks",
        "quiz",
        "cert",
        # Сложены в одну плашку trainers (вкладки Code / SQL / Git).
        "code",
        "sql",
        "git",
    }
    for app in DEFAULT_APPS:
        await cur.execute(
            """
            INSERT INTO site_apps (
                slug, title, subtitle, description, accent, emoji,
                external_href, app_path, is_visible, sort_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
            ON CONFLICT (slug) DO NOTHING
            """,
            (
                app["slug"],
                app["title"],
                app.get("subtitle", ""),
                app.get("description", ""),
                app.get("accent", "#2dd4bf"),
                app.get("emoji", ""),
                app.get("external_href", ""),
                app.get("app_path", ""),
                int(app.get("sort_order") or 0),
            ),
        )
    # Скрываем заглушки (не трогаем featured и ручные правки is_visible у них).
    if stub_hide_slugs:
        await cur.execute(
            """
            UPDATE site_apps
            SET is_visible = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE slug = ANY(%s::text[]) AND is_visible = TRUE
            """,
            (list(stub_hide_slugs),),
        )


@router.post("/auth/register")
async def register(request: Request, body: RegisterIn) -> dict[str, Any]:
    enforce_rate_limit(request, "auth")
    username = body.username.strip()
    email = str(body.email).strip().lower()
    cleaned = username.replace("_", "")
    if not cleaned or not cleaned.isalnum() or not username[0].isalnum():
        raise HTTPException(
            status_code=422,
            detail="Username: только латинские буквы, цифры и подчёркивание",
        )
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_users (email, username, password_hash, site_role)
                VALUES (%s, %s, %s, 'user')
                RETURNING id, email, username, site_role
                """,
                (email, username, _hash_password(body.password)),
            )
            row = await cur.fetchone()
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            raise HTTPException(
                status_code=409,
                detail="Email или username уже заняты",
            ) from exc
        raise
    finally:
        await release_site_db_connection(conn)

    user_id = int(row[0])
    token = _create_access_token(
        user_id=user_id,
        site_role="user",
        app_admin=[],
        username=str(row[2]),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": row[1],
            "username": row[2],
            "siteRole": "user",
            "appAdmin": [],
        },
    }


@router.post("/auth/login")
async def login(request: Request, body: LoginIn) -> dict[str, Any]:
    enforce_rate_limit(request, "auth")
    login_value = body.login.strip()
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, email, username, password_hash, site_role, is_active
                FROM site_users
                WHERE lower(email) = lower(%s) OR lower(username) = lower(%s)
                LIMIT 1
                """,
                (login_value, login_value),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)

    if not row or not _verify_password(body.password, str(row[3])):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bool(row[5]):
        raise HTTPException(status_code=403, detail="Account disabled")

    user_id = int(row[0])
    site_role = str(row[4])
    app_admin = await _app_admin_slugs(user_id)
    token = _create_access_token(
        user_id=user_id,
        site_role=site_role,
        app_admin=app_admin,
        username=str(row[2]),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": row[1],
            "username": row[2],
            "siteRole": site_role,
            "appAdmin": app_admin,
        },
    }


@router.get("/me")
async def me(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    profile_meta = await _load_profile_meta(int(user["user_id"]))
    return {
        "id": user["user_id"],
        "email": user.get("email") or "",
        "username": user["username"],
        "siteRole": user["site_role"],
        "appAdmin": user["app_admin"],
        "hasProfile": profile_meta["hasProfile"],
        "firstName": profile_meta["firstName"],
        "lastName": profile_meta["lastName"],
        "patronymic": profile_meta["patronymic"],
    }


def _parse_optional_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="birth_date must be YYYY-MM-DD") from exc






async def _load_profile_meta(user_id: int) -> dict[str, Any]:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT first_name, last_name, patronymic, phone, birth_date, city,
                       citizenship, ready_for_trips, photo_key
                FROM site_user_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        return {
            "hasProfile": False,
            "firstName": "",
            "lastName": "",
            "patronymic": "",
        }
    first_name = str(row[0] or "")
    last_name = str(row[1] or "")
    patronymic = str(row[2] or "")
    has_any = bool(
        first_name
        or last_name
        or patronymic
        or row[3]
        or row[4]
        or row[5]
        or row[6]
        or row[7]
        or row[8]
    )
    return {
        "hasProfile": has_any,
        "firstName": first_name,
        "lastName": last_name,
        "patronymic": patronymic,
    }


def _row_profile(row: tuple, *, email: str = "", has_photo: bool = False) -> dict[str, Any]:
    birth = row[5]
    return {
        "lastName": str(row[1] or ""),
        "firstName": str(row[2] or ""),
        "patronymic": str(row[3] or ""),
        "phone": str(row[4] or ""),
        "birthDate": birth.isoformat() if hasattr(birth, "isoformat") else (str(birth) if birth else None),
        "city": str(row[6] or ""),
        "citizenship": str(row[7] or ""),
        "readyForTrips": bool(row[8]),
        "hasPhoto": has_photo or bool(row[9]),
        "email": email,
        "updatedAt": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10] or ""),
    }


def _empty_profile(*, email: str = "") -> dict[str, Any]:
    return {
        "lastName": "",
        "firstName": "",
        "patronymic": "",
        "phone": "",
        "birthDate": None,
        "city": "",
        "citizenship": "",
        "readyForTrips": False,
        "hasPhoto": False,
        "email": email,
        "updatedAt": None,
    }








async def _fetch_profile_row(user_id: int) -> Optional[tuple]:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, last_name, first_name, patronymic, phone, birth_date,
                       city, citizenship, ready_for_trips, photo_key, updated_at
                FROM site_user_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return await cur.fetchone()
    finally:
        await release_site_db_connection(conn)




@router.get("/apps")
async def list_apps() -> dict[str, Any]:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT slug, title, subtitle, description, accent, emoji,
                       external_href, app_path, is_visible, sort_order, updated_at
                FROM site_apps
                WHERE is_visible = TRUE
                ORDER BY sort_order ASC, slug ASC
                """
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {"apps": [_row_app(row) for row in rows]}


@router.get("/admin/apps")
async def admin_list_apps(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    """Все плашки включая скрытые — только супер-админ."""
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT slug, title, subtitle, description, accent, emoji,
                       external_href, app_path, is_visible, sort_order, updated_at
                FROM site_apps
                ORDER BY sort_order ASC, slug ASC
                """
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {"apps": [_row_app(row) for row in rows]}


@router.put("/admin/apps/reorder")
async def reorder_apps(
    body: AppsReorderIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    slugs = [s.strip() for s in body.slugs if s and s.strip()]
    if not slugs:
        raise HTTPException(status_code=422, detail="slugs required")
    if len(slugs) != len(set(slugs)):
        raise HTTPException(status_code=422, detail="Duplicate slugs")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT slug FROM site_apps")
            existing = {str(r[0]) for r in await cur.fetchall()}
            missing = [s for s in slugs if s not in existing]
            if missing:
                raise HTTPException(status_code=404, detail=f"Unknown apps: {', '.join(missing)}")
            for index, slug in enumerate(slugs, start=1):
                await cur.execute(
                    """
                    UPDATE site_apps
                    SET sort_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE slug = %s
                    """,
                    (index, slug),
                )
            # Скрытые/не перечисленные — в конец, порядок сохраняем
            remainder = sorted(existing - set(slugs))
            base = len(slugs)
            for offset, slug in enumerate(remainder, start=1):
                await cur.execute(
                    """
                    UPDATE site_apps
                    SET sort_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE slug = %s
                    """,
                    (base + offset, slug),
                )
            await cur.execute(
                """
                SELECT slug, title, subtitle, description, accent, emoji,
                       external_href, app_path, is_visible, sort_order, updated_at
                FROM site_apps
                ORDER BY sort_order ASC, slug ASC
                """
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {"apps": [_row_app(row) for row in rows]}


@router.post("/apps")
async def create_app(
    body: AppCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    slug = body.slug.strip().lower()
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            if body.sort_order is None:
                await cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM site_apps")
                sort_row = await cur.fetchone()
                sort_order = int(sort_row[0] or 1)
            else:
                sort_order = int(body.sort_order)
            try:
                await cur.execute(
                    """
                    INSERT INTO site_apps (
                        slug, title, subtitle, description, accent, emoji,
                        external_href, app_path, is_visible, sort_order
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING slug, title, subtitle, description, accent, emoji,
                              external_href, app_path, is_visible, sort_order, updated_at
                    """,
                    (
                        slug,
                        body.title.strip(),
                        body.subtitle.strip(),
                        body.description,
                        body.accent.strip() or "#2dd4bf",
                        body.emoji.strip(),
                        body.external_href.strip(),
                        body.app_path.strip(),
                        body.is_visible,
                        sort_order,
                    ),
                )
            except Exception as exc:
                msg = str(exc).lower()
                if "unique" in msg or "duplicate" in msg:
                    raise HTTPException(status_code=409, detail="Slug уже занят") from exc
                raise
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return _row_app(row)


@router.delete("/apps/{slug}")
async def delete_app(
    slug: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM site_apps WHERE slug = %s RETURNING slug", (slug,))
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="App not found")
    return {"ok": True, "slug": slug}


@router.get("/apps/{slug}")
async def get_app(
    slug: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    allow_hidden = False
    token = _bearer_token(authorization)
    if token:
        try:
            user = await _require_user(authorization)
            allow_hidden = _can_manage_app(user, slug)
        except HTTPException:
            allow_hidden = False
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT slug, title, subtitle, description, accent, emoji,
                       external_href, app_path, is_visible, sort_order, updated_at
                FROM site_apps WHERE slug = %s
                """,
                (slug,),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="App not found")
    if not bool(row[8]) and not allow_hidden:
        raise HTTPException(status_code=404, detail="App not found")
    return _row_app(row)


@router.patch("/apps/{slug}")
async def patch_app(
    slug: str,
    body: AppUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if not _can_manage_app(user, slug):
        raise HTTPException(status_code=403, detail="No access to this app")
    updates: dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.subtitle is not None:
        updates["subtitle"] = body.subtitle
    if body.description is not None:
        updates["description"] = body.description
    if body.accent is not None:
        updates["accent"] = body.accent
    if body.emoji is not None:
        updates["emoji"] = body.emoji
    if body.external_href is not None:
        updates["external_href"] = body.external_href
    if body.app_path is not None:
        updates["app_path"] = body.app_path
    if body.is_visible is not None:
        if not _is_super_admin(user) and body.is_visible is False:
            # админ сервиса может скрыть только свою плашку; супер — любую
            pass
        updates["is_visible"] = body.is_visible
    if body.sort_order is not None:
        if not _is_super_admin(user):
            raise HTTPException(status_code=403, detail="Только супер-админ меняет порядок плашек")
        updates["sort_order"] = int(body.sort_order)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")

    sets = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [slug]
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE site_apps
                SET {sets}, updated_at = CURRENT_TIMESTAMP
                WHERE slug = %s
                RETURNING slug, title, subtitle, description, accent, emoji,
                          external_href, app_path, is_visible, sort_order, updated_at
                """,
                values,
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="App not found")
    return _row_app(row)


@router.get("/apps/{slug}/posts")
async def list_posts(
    slug: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    include_drafts = False
    token = _bearer_token(authorization)
    if token:
        try:
            user = await _require_user(authorization)
            include_drafts = _can_manage_app(user, slug)
        except HTTPException:
            include_drafts = False

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            if include_drafts:
                await cur.execute(
                    """
                    SELECT id, app_slug, slug, title, body, is_published,
                           published_at, updated_at
                    FROM site_posts
                    WHERE app_slug = %s
                    ORDER BY published_at DESC, id DESC
                    """,
                    (slug,),
                )
            else:
                await cur.execute(
                    """
                    SELECT id, app_slug, slug, title, body, is_published,
                           published_at, updated_at
                    FROM site_posts
                    WHERE app_slug = %s AND is_published = TRUE
                      AND published_at <= CURRENT_TIMESTAMP
                    ORDER BY published_at DESC, id DESC
                    """,
                    (slug,),
                )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {"posts": [_row_post(row) for row in rows]}


@router.get("/apps/{slug}/posts/{post_slug}")
async def get_post(slug: str, post_slug: str) -> dict[str, Any]:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, app_slug, slug, title, body, is_published,
                       published_at, updated_at
                FROM site_posts
                WHERE app_slug = %s AND slug = %s
                  AND is_published = TRUE AND published_at <= CURRENT_TIMESTAMP
                """,
                (slug, post_slug),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return _row_post(row)


@router.put("/apps/{slug}/posts/{post_slug}")
async def upsert_post(
    slug: str,
    post_slug: str,
    body: PostIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if not _can_manage_app(user, slug):
        raise HTTPException(status_code=403, detail="No access to this app")
    final_slug = (body.slug or post_slug).strip()
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_posts (app_slug, slug, title, body, is_published, published_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (app_slug, slug) DO UPDATE
                SET title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    is_published = EXCLUDED.is_published,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, app_slug, slug, title, body, is_published, published_at, updated_at
                """,
                (slug, final_slug, body.title, body.body, body.is_published),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return _row_post(row)


@router.delete("/apps/{slug}/posts/{post_slug}")
async def delete_post(
    slug: str,
    post_slug: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if not _can_manage_app(user, slug):
        raise HTTPException(status_code=403, detail="No access to this app")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_posts
                WHERE app_slug = %s AND slug = %s
                RETURNING id
                """,
                (slug, post_slug),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True, "id": int(row[0])}


@router.post("/contact")
async def submit_contact(request: Request, body: ContactIn) -> dict[str, Any]:
    enforce_rate_limit(request, "contact")
    name = body.name.strip()
    message = body.message.strip()
    app_slug = body.app_slug.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_contacts (app_slug, name, email, message)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (app_slug, name, str(body.email), message),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return {
        "ok": True,
        "id": row[0],
        "created_at": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
    }


async def _get_setting(key: str, default: Any = None) -> Any:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT value FROM site_settings WHERE key = %s", (key,))
            row = await cur.fetchone()
            if not row:
                return default
            value = row[0]
            if isinstance(value, (dict, list, bool, int, float)) or value is None:
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
    finally:
        await release_site_db_connection(conn)


async def _set_setting(key: str, value: Any) -> Any:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_settings (key, value, updated_at)
                VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
                RETURNING value
                """,
                (key, json.dumps(value, ensure_ascii=False)),
            )
            row = await cur.fetchone()
            return row[0] if row else value
    finally:
        await release_site_db_connection(conn)


SPOTLIGHT_LIMIT = 5
SPOTLIGHT_EXCERPT_LEN = 220


def _plain_from_post_body(text: str) -> str:
    """Extract plain text from legacy markdown or structured JSON body."""
    raw = (text or "").strip()
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and int(data.get("version") or 0) == 1:
                intro = str(data.get("intro") or "").strip()
                if intro:
                    return intro
                sections = data.get("sections") or []
                if isinstance(sections, list) and sections:
                    first = sections[0] if isinstance(sections[0], dict) else {}
                    body = str(first.get("body") or "").strip()
                    if body:
                        return body
                summary = data.get("summary") or []
                if isinstance(summary, list) and summary:
                    return str(summary[0] or "")
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return raw


def _crop_excerpt(text: str, max_len: int = SPOTLIGHT_EXCERPT_LEN) -> str:
    """Короткий кроп из markdown/plain/structured JSON для ленты и спотлайта."""
    raw = _plain_from_post_body(text).replace("\r\n", "\n")
    raw = re.sub(r"```[\s\S]*?```", " ", raw)
    raw = re.sub(r"`([^`]+)`", r"\1", raw)
    raw = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", raw)
    raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    raw = re.sub(r"^#{1,6}\s+", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"[*_~>#-]+", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) <= max_len:
        return raw
    cut = raw[: max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;: ") + "…"


async def _spotlight_items(
    limit: int = SPOTLIGHT_LIMIT,
    curated_keys: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    keys = [k.strip() for k in (curated_keys or []) if isinstance(k, str) and k.strip()]
    keys = keys[:limit]
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            if keys:
                pairs: list[tuple[str, str]] = []
                for key in keys:
                    if "/" not in key:
                        continue
                    app_slug, post_slug = key.split("/", 1)
                    pairs.append((app_slug.strip(), post_slug.strip()))
                rows: list[tuple] = []
                for app_slug, post_slug in pairs:
                    await cur.execute(
                        """
                        SELECT p.app_slug, p.slug, p.title, p.body, p.published_at,
                               a.title, a.emoji, a.accent, a.is_visible
                        FROM site_posts p
                        JOIN site_apps a ON a.slug = p.app_slug
                        WHERE p.app_slug = %s AND p.slug = %s
                          AND p.is_published = TRUE
                          AND p.published_at <= CURRENT_TIMESTAMP
                          AND a.is_visible = TRUE
                        """,
                        (app_slug, post_slug),
                    )
                    row = await cur.fetchone()
                    if row:
                        rows.append(row)
            else:
                await cur.execute(
                    """
                    SELECT p.app_slug, p.slug, p.title, p.body, p.published_at,
                           a.title, a.emoji, a.accent, a.is_visible
                    FROM site_posts p
                    JOIN site_apps a ON a.slug = p.app_slug
                    WHERE p.is_published = TRUE
                      AND p.published_at <= CURRENT_TIMESTAMP
                      AND a.is_visible = TRUE
                    ORDER BY p.published_at DESC, p.id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)

    items: list[dict[str, Any]] = []
    for row in rows:
        app_slug = str(row[0])
        post_slug = str(row[1])
        items.append(
            {
                "appSlug": app_slug,
                "postSlug": post_slug,
                "title": str(row[2]),
                "excerpt": _crop_excerpt(str(row[3] or "")),
                "publishedAt": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                "appTitle": str(row[5] or app_slug),
                "emoji": str(row[6] or ""),
                "accent": str(row[7] or "#2dd4bf"),
                "href": f"/blog/{app_slug}/{post_slug}",
            }
        )
    return items


def _normalize_curated_keys(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        key = item.strip()
        if not key or "/" not in key:
            continue
        out.append(key)
        if len(out) >= SPOTLIGHT_LIMIT:
            break
    return out


@router.get("/posts/latest")
async def list_latest_posts(limit: int = 5) -> dict[str, Any]:
    """Пять самых свежих опубликованных статей из всех блогов витрины."""
    safe_limit = max(1, min(int(limit or 5), 20))
    items = await _spotlight_items(limit=safe_limit, curated_keys=None)
    return {"items": items}


@router.get("/promo")
async def get_promo() -> dict[str, Any]:
    """Спотлайт: настройки + до 5 карточек (ручной curatedKeys или авто по дате)."""
    raw = await _get_setting(SITE_PROMO_KEY, DEFAULT_PROMO)
    data = DEFAULT_PROMO.copy()
    if isinstance(raw, dict):
        data.update({k: raw[k] for k in DEFAULT_PROMO if k in raw})
        if "curatedKeys" in raw:
            data["curatedKeys"] = _normalize_curated_keys(raw.get("curatedKeys"))
    data["enabled"] = bool(data.get("enabled", True))
    data["eyebrow"] = str(data.get("eyebrow") or DEFAULT_PROMO["eyebrow"])
    data["curatedKeys"] = _normalize_curated_keys(data.get("curatedKeys"))
    data["items"] = (
        await _spotlight_items(curated_keys=data["curatedKeys"]) if data["enabled"] else []
    )
    return data


@router.put("/promo")
async def put_promo(
    body: PromoIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    payload = body.model_dump()
    payload["curatedKeys"] = _normalize_curated_keys(payload.get("curatedKeys"))
    await _set_setting(SITE_PROMO_KEY, payload)
    result = payload.copy()
    result["items"] = (
        await _spotlight_items(curated_keys=payload["curatedKeys"])
        if payload.get("enabled", True)
        else []
    )
    return result


def _strip_learning_map_meta(markdown: str) -> str:
    text = (markdown or "").replace("\r\n", "\n").lstrip("\ufeff")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :].lstrip("\n")
    text = re.sub(r"%%[\s\S]*?%%", "\n", text)
    return text.strip() + ("\n" if text.strip() else "")


def _validate_learning_map_markdown(markdown: str) -> str:
    cleaned = _strip_learning_map_meta(markdown)
    if len(cleaned) > LEARNING_MAP_MAX_CHARS:
        raise HTTPException(status_code=400, detail="Markdown слишком большой")
    if not re.search(r"(?m)^#{1,6}\s+\S", cleaned):
        raise HTTPException(
            status_code=400,
            detail="В файле нужен хотя бы один заголовок Markdown (# …)",
        )
    if not re.search(r"(?m)^##\s+\S", cleaned):
        raise HTTPException(
            status_code=400,
            detail="Нужна хотя бы одна ветка второго уровня (## …)",
        )
    return cleaned


@router.get("/learning-map")
async def get_learning_map() -> dict[str, Any]:
    """Публичная карта: custom markdown из настроек или source=default (бандл UI)."""
    raw = await _get_setting(SITE_LEARNING_MAP_KEY, None)
    if not isinstance(raw, dict):
        return {
            "source": "default",
            "markdown": "",
            "updated_at": None,
            "updated_by": None,
            "chars": 0,
        }
    markdown = str(raw.get("markdown") or "").strip()
    if not markdown:
        return {
            "source": "default",
            "markdown": "",
            "updated_at": raw.get("updated_at"),
            "updated_by": raw.get("updated_by"),
            "chars": 0,
        }
    return {
        "source": "custom",
        "markdown": markdown,
        "updated_at": raw.get("updated_at"),
        "updated_by": raw.get("updated_by"),
        "chars": len(markdown),
    }


@router.put("/learning-map")
async def put_learning_map(
    body: LearningMapIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    """Супер-админ загружает MD — карта перерисовывается у всех."""
    user = await _require_user(authorization)
    _require_super_admin(user)
    cleaned = _validate_learning_map_markdown(body.markdown)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "markdown": cleaned,
        "updated_at": now,
        "updated_by": str(user.get("username") or user.get("sub") or ""),
    }
    await _set_setting(SITE_LEARNING_MAP_KEY, payload)
    return {
        "source": "custom",
        "markdown": cleaned,
        "updated_at": now,
        "updated_by": payload["updated_by"],
        "chars": len(cleaned),
    }


@router.delete("/learning-map")
async def delete_learning_map(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    """Сброс к встроенному outline в UI."""
    user = await _require_user(authorization)
    _require_super_admin(user)
    await _set_setting(
        SITE_LEARNING_MAP_KEY,
        {
            "markdown": "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": str(user.get("username") or user.get("sub") or ""),
        },
    )
    return {
        "source": "default",
        "markdown": "",
        "updated_at": None,
        "updated_by": None,
        "chars": 0,
    }


@router.post("/admin/assign")
async def assign_app_admin(
    body: AssignAdminIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM site_users WHERE lower(username) = lower(%s)",
                (body.username.strip(),),
            )
            urow = await cur.fetchone()
            if not urow:
                raise HTTPException(status_code=404, detail="User not found")
            await cur.execute("SELECT slug FROM site_apps WHERE slug = %s", (body.app_slug,))
            arow = await cur.fetchone()
            if not arow:
                raise HTTPException(status_code=404, detail="App not found")
            await cur.execute(
                """
                INSERT INTO site_app_admins (user_id, app_slug)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (int(urow[0]), body.app_slug),
            )
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "username": body.username, "appSlug": body.app_slug}


@router.post("/admin/unassign")
async def unassign_app_admin(
    body: UnassignAdminIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM site_users WHERE lower(username) = lower(%s)",
                (body.username.strip(),),
            )
            urow = await cur.fetchone()
            if not urow:
                raise HTTPException(status_code=404, detail="User not found")
            await cur.execute(
                """
                DELETE FROM site_app_admins
                WHERE user_id = %s AND app_slug = %s
                """,
                (int(urow[0]), body.app_slug),
            )
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "username": body.username, "appSlug": body.app_slug}


@router.get("/admin/contacts")
async def list_contacts(
    authorization: Optional[str] = Header(None),
    status: Optional[str] = None,
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    status_filter = (status or "").strip().lower()
    if status_filter and status_filter not in {"new", "read", "done"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            # status может отсутствовать до patch — подстраховываемся
            await cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'site_contacts' AND column_name = 'status'
                )
                """
            )
            has_status_row = await cur.fetchone()
            has_status = bool(has_status_row and has_status_row[0])
            if has_status:
                if status_filter:
                    await cur.execute(
                        """
                        SELECT id, app_slug, name, email, message, status, created_at
                        FROM site_contacts
                        WHERE status = %s
                        ORDER BY created_at DESC
                        LIMIT 200
                        """,
                        (status_filter,),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, app_slug, name, email, message, status, created_at
                        FROM site_contacts
                        ORDER BY created_at DESC
                        LIMIT 200
                        """
                    )
                rows = await cur.fetchall()
                contacts = [
                    {
                        "id": int(row[0]),
                        "appSlug": str(row[1] or ""),
                        "name": str(row[2] or ""),
                        "email": str(row[3] or ""),
                        "message": str(row[4] or ""),
                        "status": str(row[5] or "new"),
                        "createdAt": row[6].isoformat()
                        if hasattr(row[6], "isoformat")
                        else str(row[6]),
                    }
                    for row in rows
                ]
            else:
                await cur.execute(
                    """
                    SELECT id, app_slug, name, email, message, created_at
                    FROM site_contacts
                    ORDER BY created_at DESC
                    LIMIT 200
                    """
                )
                rows = await cur.fetchall()
                contacts = [
                    {
                        "id": int(row[0]),
                        "appSlug": str(row[1] or ""),
                        "name": str(row[2] or ""),
                        "email": str(row[3] or ""),
                        "message": str(row[4] or ""),
                        "status": "new",
                        "createdAt": row[5].isoformat()
                        if hasattr(row[5], "isoformat")
                        else str(row[5]),
                    }
                    for row in rows
                ]
    finally:
        await release_site_db_connection(conn)
    return {"contacts": contacts}


@router.patch("/admin/contacts/{contact_id}")
async def patch_contact(
    contact_id: int,
    body: ContactStatusIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE site_contacts
                SET status = %s
                WHERE id = %s
                RETURNING id, app_slug, name, email, message, status, created_at
                """,
                (body.status, contact_id),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {
        "id": int(row[0]),
        "appSlug": str(row[1] or ""),
        "name": str(row[2] or ""),
        "email": str(row[3] or ""),
        "message": str(row[4] or ""),
        "status": str(row[5] or "new"),
        "createdAt": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
    }


@router.get("/admin/users")
async def list_users(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    _require_super_admin(user)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    u.id,
                    u.email,
                    u.username,
                    u.site_role,
                    u.is_active,
                    u.created_at,
                    COALESCE(
                        ARRAY_AGG(a.app_slug ORDER BY a.app_slug)
                        FILTER (WHERE a.app_slug IS NOT NULL),
                        '{}'
                    ) AS app_slugs
                FROM site_users u
                LEFT JOIN site_app_admins a ON a.user_id = u.id
                GROUP BY u.id, u.email, u.username, u.site_role, u.is_active, u.created_at
                ORDER BY u.id ASC
                LIMIT 500
                """
            )
            rows = await cur.fetchall()
            users: list[dict[str, Any]] = []
            for row in rows:
                raw_apps = row[6] or []
                apps = [str(slug) for slug in raw_apps]
                users.append(
                    {
                        "id": int(row[0]),
                        "email": str(row[1] or ""),
                        "username": str(row[2] or ""),
                        "siteRole": str(row[3] or "user"),
                        "isActive": bool(row[4]),
                        "appAdmin": apps,
                        "createdAt": row[5].isoformat()
                        if hasattr(row[5], "isoformat")
                        else str(row[5]),
                    }
                )
    finally:
        await release_site_db_connection(conn)
    return {"users": users}


@router.patch("/admin/users/{user_id}")
async def patch_user(
    user_id: int,
    body: UserPatchIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    actor = await _require_user(authorization)
    _require_super_admin(actor)
    if (
        body.site_role is None
        and body.is_active is None
        and body.password is None
        and body.app_admin is None
    ):
        raise HTTPException(status_code=400, detail="Nothing to update")
    if actor["user_id"] == user_id and body.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    if actor["user_id"] == user_id and body.site_role == "user":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

    wanted_apps: Optional[list[str]] = None
    if body.app_admin is not None:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in body.app_admin:
            slug = str(raw or "").strip().lower()
            if not slug or slug in seen:
                continue
            seen.add(slug)
            cleaned.append(slug)
        wanted_apps = cleaned

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, email, username, site_role, is_active FROM site_users WHERE id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            if body.site_role is not None:
                await cur.execute(
                    """
                    UPDATE site_users
                    SET site_role = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (body.site_role, user_id),
                )
            if body.is_active is not None:
                await cur.execute(
                    """
                    UPDATE site_users
                    SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (body.is_active, user_id),
                )
            if body.password:
                await cur.execute(
                    """
                    UPDATE site_users
                    SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (_hash_password(body.password), user_id),
                )
            if wanted_apps is not None:
                if wanted_apps:
                    await cur.execute(
                        "SELECT slug FROM site_apps WHERE slug = ANY(%s::text[])",
                        (wanted_apps,),
                    )
                    existing = {str(r[0]) for r in await cur.fetchall()}
                    missing = [slug for slug in wanted_apps if slug not in existing]
                    if missing:
                        raise HTTPException(
                            status_code=404,
                            detail=f"App not found: {', '.join(missing)}",
                        )
                await cur.execute(
                    "DELETE FROM site_app_admins WHERE user_id = %s",
                    (user_id,),
                )
                for slug in wanted_apps:
                    await cur.execute(
                        """
                        INSERT INTO site_app_admins (user_id, app_slug)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (user_id, slug),
                    )
            await cur.execute(
                "SELECT id, email, username, site_role, is_active FROM site_users WHERE id = %s",
                (user_id,),
            )
            updated = await cur.fetchone()
            await cur.execute(
                "SELECT app_slug FROM site_app_admins WHERE user_id = %s ORDER BY app_slug",
                (user_id,),
            )
            apps = [str(r[0]) for r in await cur.fetchall()]
    finally:
        await release_site_db_connection(conn)
    assert updated is not None
    return {
        "id": int(updated[0]),
        "email": str(updated[1] or ""),
        "username": str(updated[2] or ""),
        "siteRole": str(updated[3] or "user"),
        "isActive": bool(updated[4]),
        "appAdmin": apps,
    }


@router.post("/me/password")
async def change_password(
    body: PasswordChangeIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT password_hash FROM site_users WHERE id = %s",
                (user["user_id"],),
            )
            row = await cur.fetchone()
            if not row or not _verify_password(body.current_password, str(row[0])):
                raise HTTPException(status_code=400, detail="Неверный текущий пароль")
            await cur.execute(
                """
                UPDATE site_users
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (_hash_password(body.new_password), user["user_id"]),
            )
    finally:
        await release_site_db_connection(conn)
    return {"ok": True}


@router.get("/me/profile")
async def get_my_profile(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    row = await _fetch_profile_row(int(user["user_id"]))
    email = str(user.get("email") or "")
    if not row:
        return _empty_profile(email=email)
    return _row_profile(row, email=email)


@router.put("/me/profile")
async def put_my_profile(
    body: ProfileUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    existing = await _fetch_profile_row(user_id)
    cur_vals = {
        "last_name": str(existing[1] or "") if existing else "",
        "first_name": str(existing[2] or "") if existing else "",
        "patronymic": str(existing[3] or "") if existing else "",
        "phone": str(existing[4] or "") if existing else "",
        "birth_date": existing[5] if existing else None,
        "city": str(existing[6] or "") if existing else "",
        "citizenship": str(existing[7] or "") if existing else "",
        "ready_for_trips": bool(existing[8]) if existing else False,
        "photo_key": str(existing[9] or "") if existing else "",
    }
    if body.last_name is not None:
        cur_vals["last_name"] = body.last_name.strip()
    if body.first_name is not None:
        cur_vals["first_name"] = body.first_name.strip()
    if body.patronymic is not None:
        cur_vals["patronymic"] = body.patronymic.strip()
    if body.phone is not None:
        cur_vals["phone"] = body.phone.strip()
    if body.birth_date is not None:
        cur_vals["birth_date"] = _parse_optional_date(body.birth_date)
    if body.city is not None:
        cur_vals["city"] = body.city.strip()
    if body.citizenship is not None:
        cur_vals["citizenship"] = body.citizenship.strip()
    if body.ready_for_trips is not None:
        cur_vals["ready_for_trips"] = bool(body.ready_for_trips)

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_user_profiles (
                    user_id, last_name, first_name, patronymic, phone, birth_date,
                    city, citizenship, ready_for_trips, photo_key, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    last_name = EXCLUDED.last_name,
                    first_name = EXCLUDED.first_name,
                    patronymic = EXCLUDED.patronymic,
                    phone = EXCLUDED.phone,
                    birth_date = EXCLUDED.birth_date,
                    city = EXCLUDED.city,
                    citizenship = EXCLUDED.citizenship,
                    ready_for_trips = EXCLUDED.ready_for_trips,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING user_id, last_name, first_name, patronymic, phone, birth_date,
                          city, citizenship, ready_for_trips, photo_key, updated_at
                """,
                (
                    user_id,
                    cur_vals["last_name"],
                    cur_vals["first_name"],
                    cur_vals["patronymic"],
                    cur_vals["phone"],
                    cur_vals["birth_date"],
                    cur_vals["city"],
                    cur_vals["citizenship"],
                    cur_vals["ready_for_trips"],
                    cur_vals["photo_key"],
                ),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    assert row is not None
    return _row_profile(row, email=str(user.get("email") or ""))


@router.post("/me/photo")
async def upload_my_photo(
    photo: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if not photo.filename:
        raise HTTPException(status_code=400, detail="No file name")
    ext = Path(photo.filename).suffix.lower()
    if ext not in ALLOWED_RESUME_PHOTO_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed formats: {', '.join(sorted(ALLOWED_RESUME_PHOTO_EXT))}",
        )
    raw = await read_upload_limited(
        photo, max_bytes=settings.MAX_UPLOAD_IMAGE_BYTES, label="Photo"
    )
    content = process_profile_photo(raw)
    name = f"{uuid.uuid4().hex}.jpg"
    key = f"{S3_SITE_RESUME_PREFIX}/{user_id}/{name}"
    storage = get_storage()
    if storage:
        await storage.put(key, content, content_type="image/jpeg")
        photo_key = key
    else:
        target_dir = UPLOADS_SITE_RESUME_DIR / str(user_id)
        await async_fs.makedirs(target_dir)
        await async_fs.write_bytes(target_dir / name, content)
        photo_key = f"local:{user_id}/{name}"

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_user_profiles (user_id, photo_key, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    photo_key = EXCLUDED.photo_key,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, photo_key),
            )
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "hasPhoto": True}


@router.get("/me/photo")
async def get_my_photo(authorization: Optional[str] = Header(None)) -> Response:
    user = await _require_user(authorization)
    row = await _fetch_profile_row(int(user["user_id"]))
    if not row or not row[9]:
        raise HTTPException(status_code=404, detail="Photo not found")
    photo_key = str(row[9])
    media = "image/jpeg"
    if photo_key.endswith(".png"):
        media = "image/png"
    elif photo_key.endswith(".webp"):
        media = "image/webp"

    if photo_key.startswith("local:"):
        rel = photo_key[len("local:") :]
        if ".." in rel or rel.startswith("/") or "\\" in rel:
            raise HTTPException(status_code=400, detail="Invalid photo key")
        path = UPLOADS_SITE_RESUME_DIR / rel
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Photo not found")
        data = path.read_bytes()
        return Response(content=data, media_type=media)

    storage = get_storage()
    if not storage:
        raise HTTPException(status_code=404, detail="Photo storage unavailable")
    try:
        if hasattr(storage, "get_bytes"):
            data = await storage.get_bytes(photo_key)
        else:
            data = await storage.get(photo_key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Photo not found") from exc
    if not data:
        raise HTTPException(status_code=404, detail="Photo not found")
    return Response(content=data, media_type=media)


@router.post("/auth/forgot-password")
async def forgot_password(request: Request, body: PasswordForgotIn) -> dict[str, Any]:
    """Создаёт reset-токен. Токен в JSON только при DEV_EXPOSE_RESET_TOKEN=true."""
    enforce_rate_limit(request, "auth")
    login = body.login.strip()
    conn = await get_site_db_connection()
    token: Optional[str] = None
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM site_users
                WHERE lower(email) = lower(%s) OR lower(username) = lower(%s)
                """,
                (login, login),
            )
            row = await cur.fetchone()
            if row:
                token = py_secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
                expires = datetime.now(timezone.utc) + timedelta(hours=2)
                await cur.execute(
                    """
                    INSERT INTO site_password_resets (user_id, token_hash, expires_at)
                    VALUES (%s, %s, %s)
                    """,
                    (int(row[0]), token_hash, expires),
                )
    finally:
        await release_site_db_connection(conn)
    result: dict[str, Any] = {
        "ok": True,
        "detail": (
            "Если аккаунт существует, инструкции по сбросу пароля будут отправлены "
            "(SMTP пока не подключён)."
        ),
    }
    if token and bool(settings.DEV_EXPOSE_RESET_TOKEN):
        result["resetToken"] = token
    return result


@router.post("/auth/reset-password")
async def reset_password(request: Request, body: PasswordResetIn) -> dict[str, Any]:
    enforce_rate_limit(request, "auth")
    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id FROM site_password_resets
                WHERE token_hash = %s
                  AND used_at IS NULL
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (token_hash,),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="Недействительный или просроченный токен")
            await cur.execute(
                """
                UPDATE site_users
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (_hash_password(body.new_password), int(row[1])),
            )
            await cur.execute(
                """
                UPDATE site_password_resets
                SET used_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (int(row[0]),),
            )
    finally:
        await release_site_db_connection(conn)
    return {"ok": True}


@router.get("/learn/progress")
async def get_learn_progress(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT slug, completed_at
                FROM site_learn_progress
                WHERE user_id = %s
                ORDER BY completed_at DESC
                """,
                (user["user_id"],),
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {
        "items": [
            {
                "slug": str(row[0]),
                "completedAt": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
            }
            for row in rows
        ]
    }


@router.put("/learn/progress")
async def put_learn_progress(
    body: LearnProgressIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    slug = body.slug.strip()
    if not slug:
        raise HTTPException(status_code=400, detail="slug required")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            if body.completed:
                await cur.execute(
                    """
                    INSERT INTO site_learn_progress (user_id, slug, completed_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, slug) DO UPDATE
                        SET completed_at = CURRENT_TIMESTAMP
                    RETURNING slug, completed_at
                    """,
                    (user["user_id"], slug),
                )
                row = await cur.fetchone()
                return {
                    "slug": str(row[0]),
                    "completedAt": row[1].isoformat()
                    if hasattr(row[1], "isoformat")
                    else str(row[1]),
                    "completed": True,
                }
            await cur.execute(
                """
                DELETE FROM site_learn_progress
                WHERE user_id = %s AND slug = %s
                """,
                (user["user_id"], slug),
            )
            return {"slug": slug, "completedAt": None, "completed": False}
    finally:
        await release_site_db_connection(conn)


def _anki_next_interval(ease: int, prev_interval: int, repetitions: int) -> tuple[int, int]:
    """Simplified SM-2-ish: returns (interval_days, next_repetitions)."""
    if ease <= 1:
        return 0, 0
    if repetitions <= 0:
        return (1 if ease == 2 else 3 if ease == 3 else 4), 1
    if repetitions == 1:
        return (3 if ease == 2 else 7 if ease == 3 else 10), 2
    factor = 1.3 if ease == 2 else 2.0 if ease == 3 else 2.5
    nxt = max(1, int(round(max(prev_interval, 1) * factor)))
    return nxt, repetitions + 1


@router.get("/study/summary")
async def get_study_summary(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    """Сводка для кабинета учащегося: тесты и anki."""
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*)::int,
                       COALESCE(SUM(score), 0)::int,
                       COALESCE(SUM(total), 0)::int,
                       MAX(finished_at)
                FROM site_quiz_attempts
                WHERE user_id = %s
                """,
                (user["user_id"],),
            )
            quiz_row = await cur.fetchone()
            await cur.execute(
                """
                SELECT source_key, score, total, finished_at
                FROM site_quiz_attempts
                WHERE user_id = %s
                ORDER BY finished_at DESC
                LIMIT 8
                """,
                (user["user_id"],),
            )
            recent_quiz = await cur.fetchall()
            await cur.execute(
                """
                SELECT source_key, score, total, finished_at
                FROM (
                    SELECT source_key, score, total, finished_at,
                           ROW_NUMBER() OVER (
                               PARTITION BY source_key
                               ORDER BY
                                   CASE
                                       WHEN total > 0 THEN score::float / total
                                       ELSE 0
                                   END DESC,
                                   finished_at DESC
                           ) AS rn
                    FROM site_quiz_attempts
                    WHERE user_id = %s
                ) ranked
                WHERE rn = 1
                ORDER BY source_key
                """,
                (user["user_id"],),
            )
            best_quiz = await cur.fetchall()
            await cur.execute(
                """
                SELECT COUNT(*)::int,
                       COUNT(*) FILTER (WHERE due_at <= CURRENT_TIMESTAMP)::int,
                       COUNT(*) FILTER (WHERE repetitions > 0)::int
                FROM site_anki_cards
                WHERE user_id = %s
                """,
                (user["user_id"],),
            )
            anki_row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)

    quiz_attempts = int(quiz_row[0] or 0) if quiz_row else 0
    quiz_score_sum = int(quiz_row[1] or 0) if quiz_row else 0
    quiz_total_sum = int(quiz_row[2] or 0) if quiz_row else 0
    last_quiz_at = None
    if quiz_row and quiz_row[3] is not None:
        last_quiz_at = (
            quiz_row[3].isoformat() if hasattr(quiz_row[3], "isoformat") else str(quiz_row[3])
        )

    def _quiz_row_payload(row: Any) -> dict[str, Any]:
        total = int(row[2] or 0)
        score = int(row[1] or 0)
        return {
            "sourceKey": str(row[0]),
            "score": score,
            "total": total,
            "percent": round((score / total) * 100) if total else 0,
            "finishedAt": row[3].isoformat()
            if hasattr(row[3], "isoformat")
            else str(row[3]),
        }

    return {
        "quiz": {
            "attempts": quiz_attempts,
            "scoreSum": quiz_score_sum,
            "totalSum": quiz_total_sum,
            "avgPercent": round((quiz_score_sum / quiz_total_sum) * 100) if quiz_total_sum else 0,
            "lastAt": last_quiz_at,
            "recent": [_quiz_row_payload(row) for row in recent_quiz],
            "best": [_quiz_row_payload(row) for row in best_quiz],
        },
        "anki": {
            "cards": int(anki_row[0] or 0) if anki_row else 0,
            "due": int(anki_row[1] or 0) if anki_row else 0,
            "learning": int(anki_row[2] or 0) if anki_row else 0,
        },
    }


@router.post("/study/quiz")
async def post_quiz_attempt(
    body: QuizAttemptIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    source_key = body.source_key.strip()
    if not source_key:
        raise HTTPException(status_code=400, detail="source_key required")
    total = max(body.total, 0)
    score = min(max(body.score, 0), total if total else body.score)
    answers_json = json.dumps(body.answers if isinstance(body.answers, list) else [])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_quiz_attempts
                    (user_id, source_type, source_key, score, total, answers, finished_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, CURRENT_TIMESTAMP)
                RETURNING id, finished_at
                """,
                (user["user_id"], body.source_type, source_key, score, total, answers_json),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return {
        "id": int(row[0]),
        "sourceType": body.source_type,
        "sourceKey": source_key,
        "score": score,
        "total": total,
        "finishedAt": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
    }


_CERT_POSTS_SQL = """
SELECT slug, episode,
       EXISTS (
           SELECT 1
           FROM jsonb_array_elements(
               CASE
                   WHEN jsonb_typeof(COALESCE(structured, '{}'::jsonb)->'quiz') = 'array'
                   THEN COALESCE(structured, '{}'::jsonb)->'quiz'
                   ELSE '[]'::jsonb
               END
           ) AS question
           WHERE length(btrim(COALESCE(question->>'question', ''))) > 0
             AND length(btrim(COALESCE(question->>'answer', ''))) > 0
       ) AS has_quiz
FROM learn_posts
WHERE published_at <= NOW()
ORDER BY sort_order ASC, id ASC
"""


def _iso_stamp(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _cert_track_payload(track: dict[str, Any], code: str, issued_at: str) -> dict[str, Any]:
    return {
        "id": track["id"],
        "title": track["title"],
        "done": track["done"],
        "total": track["total"],
        "earned": track["earned"],
        "quizRequired": track["quiz_required"],
        "quizPassed": track["quiz_passed"],
        "quizPercent": track["quiz_percent"],
        "quizMissing": track["quiz_missing"],
        "code": code,
        "issuedAt": issued_at,
    }


async def _load_certificate_board(cur: Any, user_id: int) -> list[dict[str, Any]]:
    await cur.execute(_CERT_POSTS_SQL)
    post_rows = await cur.fetchall()
    posts = [
        {
            "slug": str(row[0] or ""),
            "episode": str(row[1] or ""),
            "has_quiz": bool(row[2]),
        }
        for row in post_rows
    ]
    await cur.execute(
        "SELECT slug FROM site_learn_progress WHERE user_id = %s",
        (user_id,),
    )
    completed = {str(row[0]).strip().lower() for row in await cur.fetchall() if row and row[0]}
    await cur.execute(
        """
        SELECT source_key, score, total, source_type
        FROM site_quiz_attempts
        WHERE user_id = %s AND source_type IN ('learn', 'quiz_page')
        """,
        (user_id,),
    )
    learn_attempts: list[dict[str, Any]] = []
    interview_attempts: list[dict[str, Any]] = []
    for row in await cur.fetchall():
        item = {
            "source_key": str(row[0] or ""),
            "score": int(row[1] or 0),
            "total": int(row[2] or 0),
        }
        source_type = str(row[3] or "")
        if source_type == "quiz_page":
            interview_attempts.append(item)
        else:
            learn_attempts.append(item)
    board = assess_tracks(posts, completed, best_quiz_percents(learn_attempts))
    board.append(assess_interview_track(interview_attempts))
    return board


async def _resolve_certificate_holder(cur: Any, user_id: int, username: str) -> str:
    await cur.execute(
        """
        SELECT COALESCE(p.last_name, ''),
               COALESCE(p.first_name, ''),
               COALESCE(p.patronymic, ''),
               COALESCE(u.username, '')
        FROM site_users u
        LEFT JOIN site_user_profiles p ON p.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    row = await cur.fetchone()
    if not row:
        return certificate_holder_name("", "", "", username)
    return certificate_holder_name(
        str(row[0] or ""),
        str(row[1] or ""),
        str(row[2] or ""),
        str(row[3] or "") or username,
    )


async def _sync_certificates(cur: Any, user_id: int, holder_name: str) -> list[dict[str, Any]]:
    board = await _load_certificate_board(cur, user_id)
    earned_ids = [track["id"] for track in board if track["earned"]]
    if earned_ids:
        await cur.execute(
            """
            DELETE FROM site_certificates
            WHERE user_id = %s AND NOT (track_id = ANY(%s))
            """,
            (user_id, earned_ids),
        )
    else:
        await cur.execute("DELETE FROM site_certificates WHERE user_id = %s", (user_id,))

    stored: dict[str, tuple[str, str]] = {}
    holder = await _resolve_certificate_holder(cur, user_id, holder_name)
    for track in board:
        if not track["earned"]:
            continue
        code = blank_code(user_id, track["id"])
        await cur.execute(
            """
            INSERT INTO site_certificates (
                code, user_id, track_id, track_title, holder_name, episode_count, quiz_percent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, track_id) DO UPDATE SET
                track_title = EXCLUDED.track_title,
                holder_name = EXCLUDED.holder_name,
                episode_count = EXCLUDED.episode_count,
                quiz_percent = EXCLUDED.quiz_percent
            RETURNING code, issued_at
            """,
            (
                code,
                user_id,
                track["id"],
                track["title"],
                holder,
                track["total"],
                track["quiz_percent"],
            ),
        )
        saved = await cur.fetchone()
        stored[track["id"]] = (str(saved[0]), _iso_stamp(saved[1]))

    return [
        _cert_track_payload(
            track,
            stored.get(track["id"], ("", ""))[0],
            stored.get(track["id"], ("", ""))[1],
        )
        for track in board
    ]


@router.get("/learn/certificates")
async def list_certificates(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    """Выдать или снять бланки по текущему прогрессу и вернуть доску."""
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            tracks = await _sync_certificates(cur, int(user["user_id"]), str(user["username"]))
    finally:
        await release_site_db_connection(conn)
    return {"quizThreshold": CERT_QUIZ_PERCENT, "tracks": tracks}


@router.get("/learn/certificates/{code}")
async def public_certificate(code: str, request: Request) -> dict[str, Any]:
    """Публичная проверка бланка. Без сессии. Просроченный прогресс снимает бланк."""
    enforce_rate_limit(request, "public")
    normalized = (code or "").strip().upper()
    if not is_cert_code(normalized):
        raise HTTPException(status_code=404, detail="Сертификат не найден")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, track_id, holder_name, issued_at
                FROM site_certificates
                WHERE code = %s
                """,
                (normalized,),
            )
            found = await cur.fetchone()
            if not found:
                raise HTTPException(status_code=404, detail="Сертификат не найден")
            user_id = int(found[0])
            track_id = str(found[1])
            holder = await _resolve_certificate_holder(cur, user_id, str(found[2] or ""))
            board = await _load_certificate_board(cur, user_id)
            track = next((item for item in board if item["id"] == track_id and item["earned"]), None)
            if track is None:
                await cur.execute("DELETE FROM site_certificates WHERE code = %s", (normalized,))
                raise HTTPException(status_code=404, detail="Сертификат не найден")
            payload = {
                "code": normalized,
                "holderName": holder,
                "trackId": track["id"],
                "trackTitle": track["title"],
                "episodeCount": track["total"],
                "quizPercent": track["quiz_percent"],
                "quizRequired": track["quiz_required"],
                "quizThreshold": (
                    INTERVIEW_CERT_PERCENT
                    if track["id"] == INTERVIEW_TRACK_ID
                    else CERT_QUIZ_PERCENT
                ),
                "issuedAt": _iso_stamp(found[3]),
            }
    finally:
        await release_site_db_connection(conn)
    return payload


@router.get("/study/anki")
async def get_anki_cards(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT card_id, front, back, source_key, ease, interval_days,
                       repetitions, due_at, updated_at
                FROM site_anki_cards
                WHERE user_id = %s
                ORDER BY due_at ASC, updated_at DESC
                """,
                (user["user_id"],),
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {
        "cards": [
            {
                "cardId": str(row[0]),
                "front": str(row[1] or ""),
                "back": str(row[2] or ""),
                "sourceKey": str(row[3] or ""),
                "ease": int(row[4] or 0),
                "intervalDays": int(row[5] or 0),
                "repetitions": int(row[6] or 0),
                "dueAt": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
                "updatedAt": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
                "isDue": True,
            }
            for row in rows
        ]
    }


@router.put("/study/anki")
async def put_anki_review(
    body: AnkiReviewIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    card_id = body.card_id.strip()
    if not card_id:
        raise HTTPException(status_code=400, detail="card_id required")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT interval_days, repetitions
                FROM site_anki_cards
                WHERE user_id = %s AND card_id = %s
                """,
                (user["user_id"], card_id),
            )
            existing = await cur.fetchone()
            prev_interval = int(existing[0] or 0) if existing else 0
            prev_reps = int(existing[1] or 0) if existing else 0
            interval_days, repetitions = _anki_next_interval(body.ease, prev_interval, prev_reps)
            await cur.execute(
                """
                INSERT INTO site_anki_cards (
                    user_id, card_id, front, back, source_key,
                    ease, interval_days, repetitions, due_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    CURRENT_TIMESTAMP + (%s || ' days')::interval,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id, card_id) DO UPDATE
                SET front = EXCLUDED.front,
                    back = EXCLUDED.back,
                    source_key = COALESCE(NULLIF(EXCLUDED.source_key, ''), site_anki_cards.source_key),
                    ease = EXCLUDED.ease,
                    interval_days = EXCLUDED.interval_days,
                    repetitions = EXCLUDED.repetitions,
                    due_at = EXCLUDED.due_at,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING card_id, due_at, interval_days, repetitions
                """,
                (
                    user["user_id"],
                    card_id,
                    body.front[:2000],
                    body.back[:8000],
                    body.source_key.strip(),
                    body.ease,
                    interval_days,
                    repetitions,
                    str(interval_days),
                ),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return {
        "cardId": str(row[0]),
        "dueAt": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
        "intervalDays": int(row[2] or 0),
        "repetitions": int(row[3] or 0),
        "ease": body.ease,
    }


def _parse_optional_due_date(raw: Optional[str], *, allow_clear: bool = False) -> Optional[date]:
    """Parse YYYY-MM-DD. Empty string clears when allow_clear=True; otherwise None means unset."""
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        if allow_clear:
            return None
        raise HTTPException(status_code=400, detail="due_at must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="due_at must be YYYY-MM-DD") from exc


def _parse_optional_time(raw: Optional[str], *, allow_clear: bool = False):
    from datetime import time as time_cls

    if raw is None:
        return None
    value = raw.strip()
    if not value:
        if allow_clear:
            return None
        raise HTTPException(status_code=400, detail="due_time must be HH:MM")
    try:
        parts = value.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return time_cls(hour=hour, minute=minute)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail="due_time must be HH:MM") from exc


def _parse_optional_remind_at(raw: Optional[str], *, allow_clear: bool = False) -> Optional[datetime]:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        if allow_clear:
            return None
        raise HTTPException(status_code=400, detail="remind_at must be ISO datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="remind_at must be ISO datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_priority(raw: str) -> str:
    from services.task_planner import VALID_PRIORITIES

    value = (raw or "normal").strip().lower()
    if value not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="invalid priority")
    return value


def _normalize_board(raw: str) -> str:
    from services.task_planner import VALID_BOARDS

    value = (raw or "backlog").strip().lower()
    if value not in VALID_BOARDS:
        raise HTTPException(status_code=400, detail="invalid board")
    return value


def _normalize_repeat_rule(raw: str) -> str:
    from services.task_planner import VALID_REPEAT_RULES

    value = (raw or "none").strip().lower()
    if value not in VALID_REPEAT_RULES:
        raise HTTPException(status_code=400, detail="invalid repeat_rule")
    return value


def _checklist_from_db(raw: Any) -> list[dict[str, Any]]:
    from services.task_planner import normalize_checklist

    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    return normalize_checklist(raw)


def _user_task_payload(row: Any) -> dict[str, Any]:
    # id, parent_id, title, notes, tag, due_at, due_time, remind_at, priority, board,
    # checklist, repeat_rule, series_id, is_done, completed_at, sort_order, created_at, updated_at
    due = row[5]
    due_time = row[6]
    remind_at = row[7]
    completed_at = row[14]
    created_at = row[16]
    updated_at = row[17]
    series_id = row[12]
    parent_id = row[1]
    due_time_str = None
    if due_time is not None:
        if hasattr(due_time, "strftime"):
            due_time_str = due_time.strftime("%H:%M")
        else:
            due_time_str = str(due_time)[:5]
    return {
        "id": int(row[0]),
        "parentId": int(parent_id) if parent_id is not None else None,
        "title": str(row[2] or ""),
        "notes": str(row[3] or ""),
        "tag": str(row[4] or ""),
        "dueAt": due.isoformat() if hasattr(due, "isoformat") else (str(due) if due else None),
        "dueTime": due_time_str,
        "remindAt": (
            remind_at.isoformat()
            if hasattr(remind_at, "isoformat")
            else (str(remind_at) if remind_at else None)
        ),
        "priority": str(row[8] or "normal"),
        "board": str(row[9] or "backlog"),
        "checklist": _checklist_from_db(row[10]),
        "repeatRule": str(row[11] or "none"),
        "seriesId": str(series_id) if series_id else None,
        "completed": bool(row[13]),
        "completedAt": (
            completed_at.isoformat()
            if hasattr(completed_at, "isoformat")
            else (str(completed_at) if completed_at else None)
        ),
        "sortOrder": int(row[15] or 0),
        "createdAt": (
            created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        ),
        "updatedAt": (
            updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at)
        ),
        "subtasks": [],
    }


_USER_TASK_SELECT = """
SELECT id, parent_id, title, notes, tag, due_at, due_time, remind_at, priority, board,
       checklist, repeat_rule, series_id, is_done, completed_at, sort_order,
       created_at, updated_at
FROM site_user_tasks
"""

_USER_TASK_RETURNING = """
RETURNING id, parent_id, title, notes, tag, due_at, due_time, remind_at, priority, board,
          checklist, repeat_rule, series_id, is_done, completed_at, sort_order,
          created_at, updated_at
"""


def _nest_tasks(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in payloads}
    roots: list[dict[str, Any]] = []
    for item in payloads:
        parent_id = item.get("parentId")
        if parent_id and parent_id in by_id:
            by_id[parent_id].setdefault("subtasks", []).append(item)
        else:
            roots.append(item)
    return roots


async def _catch_up_recurring_tasks(cur: Any, user_id: int) -> None:
    from services.task_planner import catch_up_due_dates, reset_checklist

    await cur.execute(
        f"""
        {_USER_TASK_SELECT}
        WHERE user_id = %s
          AND parent_id IS NULL
          AND repeat_rule <> 'none'
          AND series_id IS NOT NULL
        ORDER BY series_id, due_at DESC NULLS LAST, id DESC
        """,
        (user_id,),
    )
    rows = await cur.fetchall()
    latest_by_series: dict[str, Any] = {}
    for row in rows:
        series_key = str(row[12]) if row[12] else ""
        if not series_key or series_key in latest_by_series:
            continue
        latest_by_series[series_key] = row

    today = date.today()
    for series_key, row in latest_by_series.items():
        rule = str(row[11] or "none")
        last_due = row[5]
        if last_due is None:
            continue
        if hasattr(last_due, "isoformat"):
            last_due_date = last_due
        else:
            try:
                last_due_date = date.fromisoformat(str(last_due)[:10])
            except ValueError:
                continue
        missing = catch_up_due_dates(last_due_date, rule, until=today)
        if not missing:
            continue
        checklist = json.dumps(reset_checklist(_checklist_from_db(row[10])))
        due_time = row[6]
        remind_at = None
        for due in missing:
            await cur.execute(
                f"""
                INSERT INTO site_user_tasks (
                    user_id, parent_id, title, notes, tag, due_at, due_time, remind_at,
                    priority, board, checklist, repeat_rule, series_id, is_done
                )
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, 'backlog', %s::jsonb, %s, %s, FALSE)
                {_USER_TASK_RETURNING}
                """,
                (
                    user_id,
                    str(row[2] or "")[:512],
                    str(row[3] or "")[:8000],
                    str(row[4] or "")[:64],
                    due,
                    due_time,
                    remind_at,
                    str(row[8] or "normal"),
                    checklist,
                    rule,
                    series_key,
                ),
            )


async def _spawn_next_occurrence(cur: Any, user_id: int, source_row: Any) -> None:
    from services.task_planner import next_due_date, reset_checklist

    rule = str(source_row[11] or "none")
    if rule == "none":
        return
    series_id = source_row[12]
    if series_id is None:
        series_id = uuid.uuid4()
        await cur.execute(
            """
            UPDATE site_user_tasks
            SET series_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s
            """,
            (str(series_id), int(source_row[0]), user_id),
        )
    due = source_row[5]
    base_due = None
    if due is not None:
        base_due = due if hasattr(due, "isoformat") else date.fromisoformat(str(due)[:10])
    nxt = next_due_date(base_due, rule, from_day=date.today())
    if nxt is None:
        return
    # Skip if an open occurrence with this due already exists
    await cur.execute(
        """
        SELECT 1 FROM site_user_tasks
        WHERE user_id = %s AND series_id = %s AND due_at = %s AND is_done = FALSE
        LIMIT 1
        """,
        (user_id, str(series_id), nxt),
    )
    if await cur.fetchone():
        return
    checklist = json.dumps(reset_checklist(_checklist_from_db(source_row[10])))
    await cur.execute(
        f"""
        INSERT INTO site_user_tasks (
            user_id, parent_id, title, notes, tag, due_at, due_time, remind_at,
            priority, board, checklist, repeat_rule, series_id, is_done
        )
        VALUES (%s, NULL, %s, %s, %s, %s, %s, NULL, %s, 'backlog', %s::jsonb, %s, %s, FALSE)
        {_USER_TASK_RETURNING}
        """,
        (
            user_id,
            str(source_row[2] or "")[:512],
            str(source_row[3] or "")[:8000],
            str(source_row[4] or "")[:64],
            nxt,
            source_row[6],
            str(source_row[8] or "normal"),
            checklist,
            rule,
            str(series_id),
        ),
    )


@router.get("/tasks")
async def list_user_tasks(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    """Personal task tracker — independent of Learn progress."""
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await _catch_up_recurring_tasks(cur, user_id)
            await cur.execute(
                f"""
                {_USER_TASK_SELECT}
                WHERE user_id = %s
                ORDER BY is_done ASC,
                         due_at ASC NULLS LAST,
                         sort_order ASC,
                         created_at DESC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    payloads = [_user_task_payload(row) for row in rows]
    return {"items": _nest_tasks(payloads)}


@router.post("/tasks")
async def create_user_task(
    body: UserTaskCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    from services.task_planner import (
        board_for_completion,
        due_hint_for_board,
        normalize_checklist,
    )

    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    due_at = None
    if body.due_at is not None and body.due_at.strip():
        due_at = _parse_optional_due_date(body.due_at)
    due_time = None
    if body.due_time is not None and body.due_time.strip():
        due_time = _parse_optional_time(body.due_time)
    remind_at = None
    if body.remind_at is not None and body.remind_at.strip():
        remind_at = _parse_optional_remind_at(body.remind_at)
    notes = (body.notes or "").strip()[:8000]
    tag = (body.tag or "").strip()[:64]
    priority = _normalize_priority(body.priority)
    board = _normalize_board(body.board)
    repeat_rule = _normalize_repeat_rule(body.repeat_rule)
    checklist = normalize_checklist([item.model_dump() for item in body.checklist])
    parent_id = body.parent_id if body.parent_id and body.parent_id > 0 else None
    series_id = str(uuid.uuid4()) if repeat_rule != "none" else None
    is_done = board == "done"
    completed_at = datetime.now(timezone.utc) if is_done else None
    board = board_for_completion(is_done, board)
    if due_at is None:
        due_at = due_hint_for_board(board)

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            if parent_id is not None:
                await cur.execute(
                    """
                    SELECT id FROM site_user_tasks
                    WHERE id = %s AND user_id = %s AND parent_id IS NULL
                    """,
                    (parent_id, user_id),
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=400, detail="parent task not found")
                # Subtasks do not carry their own recurrence series
                series_id = None
                repeat_rule = "none"
            await cur.execute(
                f"""
                INSERT INTO site_user_tasks (
                    user_id, parent_id, title, notes, tag, due_at, due_time, remind_at,
                    priority, board, checklist, repeat_rule, series_id, is_done, completed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                {_USER_TASK_RETURNING}
                """,
                (
                    user_id,
                    parent_id,
                    title[:512],
                    notes,
                    tag,
                    due_at,
                    due_time,
                    remind_at,
                    priority,
                    board,
                    json.dumps(checklist),
                    repeat_rule,
                    series_id,
                    is_done,
                    completed_at,
                ),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return _user_task_payload(row)


@router.patch("/tasks/{task_id}")
async def update_user_task(
    task_id: int,
    body: UserTaskUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    from services.task_planner import (
        board_for_completion,
        due_hint_for_board,
        normalize_checklist,
    )

    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if task_id <= 0:
        raise HTTPException(status_code=400, detail="invalid task id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                {_USER_TASK_SELECT}
                WHERE id = %s AND user_id = %s
                """,
                (task_id, user_id),
            )
            existing = await cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="task not found")

            parent_id = existing[1]
            title = str(existing[2] or "")
            notes = str(existing[3] or "")
            tag = str(existing[4] or "")
            due_at = existing[5]
            due_time = existing[6]
            remind_at = existing[7]
            priority = str(existing[8] or "normal")
            board = str(existing[9] or "backlog")
            checklist = _checklist_from_db(existing[10])
            repeat_rule = str(existing[11] or "none")
            series_id = existing[12]
            is_done = bool(existing[13])
            completed_at = existing[14]
            sort_order = int(existing[15] or 0)
            was_done = is_done

            if body.title is not None:
                title = body.title.strip()
                if not title:
                    raise HTTPException(status_code=400, detail="title required")
                title = title[:512]
            if body.notes is not None:
                notes = body.notes.strip()[:8000]
            if body.tag is not None:
                tag = body.tag.strip()[:64]
            if body.due_at is not None:
                if body.due_at.strip() == "":
                    due_at = None
                else:
                    due_at = _parse_optional_due_date(body.due_at)
            if body.due_time is not None:
                if body.due_time.strip() == "":
                    due_time = None
                else:
                    due_time = _parse_optional_time(body.due_time)
            if body.remind_at is not None:
                if body.remind_at.strip() == "":
                    remind_at = None
                else:
                    remind_at = _parse_optional_remind_at(body.remind_at)
            if body.priority is not None:
                priority = _normalize_priority(body.priority)
            if body.board is not None:
                board = _normalize_board(body.board)
                hint = due_hint_for_board(board)
                if hint is not None and due_at is None:
                    due_at = hint
                if board == "done":
                    is_done = True
                elif board != "done" and is_done and body.completed is None:
                    is_done = False
            if body.checklist is not None:
                checklist = normalize_checklist([item.model_dump() for item in body.checklist])
            if body.repeat_rule is not None:
                repeat_rule = _normalize_repeat_rule(body.repeat_rule)
                if repeat_rule != "none" and series_id is None and parent_id is None:
                    series_id = uuid.uuid4()
                if repeat_rule == "none":
                    series_id = None
            if body.parent_id is not None:
                if body.parent_id <= 0:
                    parent_id = None
                else:
                    if body.parent_id == task_id:
                        raise HTTPException(status_code=400, detail="task cannot be its parent")
                    await cur.execute(
                        """
                        SELECT id FROM site_user_tasks
                        WHERE id = %s AND user_id = %s AND parent_id IS NULL
                        """,
                        (body.parent_id, user_id),
                    )
                    if not await cur.fetchone():
                        raise HTTPException(status_code=400, detail="parent task not found")
                    parent_id = body.parent_id
                    repeat_rule = "none"
                    series_id = None
            if body.sort_order is not None:
                sort_order = int(body.sort_order)
            if body.completed is not None:
                is_done = bool(body.completed)
            board = board_for_completion(is_done, board)
            if is_done and completed_at is None:
                completed_at = datetime.now(timezone.utc)
            if not is_done:
                completed_at = None

            await cur.execute(
                f"""
                UPDATE site_user_tasks
                SET parent_id = %s,
                    title = %s,
                    notes = %s,
                    tag = %s,
                    due_at = %s,
                    due_time = %s,
                    remind_at = %s,
                    priority = %s,
                    board = %s,
                    checklist = %s::jsonb,
                    repeat_rule = %s,
                    series_id = %s,
                    is_done = %s,
                    completed_at = %s,
                    sort_order = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                {_USER_TASK_RETURNING}
                """,
                (
                    parent_id,
                    title,
                    notes,
                    tag,
                    due_at,
                    due_time,
                    remind_at,
                    priority,
                    board,
                    json.dumps(checklist),
                    repeat_rule,
                    str(series_id) if series_id else None,
                    is_done,
                    completed_at,
                    sort_order,
                    task_id,
                    user_id,
                ),
            )
            row = await cur.fetchone()
            if is_done and not was_done and parent_id is None:
                await _spawn_next_occurrence(cur, user_id, row)
    finally:
        await release_site_db_connection(conn)
    return _user_task_payload(row)


@router.delete("/tasks/{task_id}")
async def delete_user_task(
    task_id: int,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if task_id <= 0:
        raise HTTPException(status_code=400, detail="invalid task id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_user_tasks
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (task_id, user["user_id"]),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="task not found")
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "id": int(row[0])}


def _habit_payload(row: Any, *, checks: list[str], streak: int) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "title": str(row[1] or ""),
        "tag": str(row[2] or ""),
        "color": str(row[3] or ""),
        "sortOrder": int(row[4] or 0),
        "isArchived": bool(row[5]),
        "createdAt": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
        "updatedAt": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
        "checks": checks,
        "streak": streak,
    }


@router.get("/habits")
async def list_habits(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    from services.task_planner import habit_streak

    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    since = date.today() - timedelta(days=60)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, title, tag, color, sort_order, is_archived, created_at, updated_at
                FROM site_user_habits
                WHERE user_id = %s AND is_archived = FALSE
                ORDER BY sort_order ASC, id ASC
                """,
                (user_id,),
            )
            habits = await cur.fetchall()
            result: list[dict[str, Any]] = []
            for habit in habits:
                await cur.execute(
                    """
                    SELECT day FROM site_user_habit_checks
                    WHERE habit_id = %s AND day >= %s
                    ORDER BY day DESC
                    """,
                    (int(habit[0]), since),
                )
                check_rows = await cur.fetchall()
                days = [
                    (r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])[:10])
                    for r in check_rows
                ]
                day_objs = [
                    r[0] if hasattr(r[0], "isoformat") else date.fromisoformat(str(r[0])[:10])
                    for r in check_rows
                ]
                result.append(
                    _habit_payload(habit, checks=days, streak=habit_streak(day_objs))
                )
    finally:
        await release_site_db_connection(conn)
    return {"items": result}


@router.post("/habits")
async def create_habit(
    body: HabitCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_user_habits (user_id, title, tag, color)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, tag, color, sort_order, is_archived, created_at, updated_at
                """,
                (
                    user["user_id"],
                    title[:256],
                    (body.tag or "").strip()[:64],
                    (body.color or "").strip()[:32],
                ),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return _habit_payload(row, checks=[], streak=0)


@router.patch("/habits/{habit_id}")
async def update_habit(
    habit_id: int,
    body: HabitUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    from services.task_planner import habit_streak

    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if habit_id <= 0:
        raise HTTPException(status_code=400, detail="invalid habit id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, title, tag, color, sort_order, is_archived, created_at, updated_at
                FROM site_user_habits
                WHERE id = %s AND user_id = %s
                """,
                (habit_id, user_id),
            )
            existing = await cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="habit not found")
            title = str(existing[1] or "")
            tag = str(existing[2] or "")
            color = str(existing[3] or "")
            sort_order = int(existing[4] or 0)
            is_archived = bool(existing[5])
            if body.title is not None:
                title = body.title.strip()[:256]
                if not title:
                    raise HTTPException(status_code=400, detail="title required")
            if body.tag is not None:
                tag = body.tag.strip()[:64]
            if body.color is not None:
                color = body.color.strip()[:32]
            if body.sort_order is not None:
                sort_order = int(body.sort_order)
            if body.is_archived is not None:
                is_archived = bool(body.is_archived)
            await cur.execute(
                """
                UPDATE site_user_habits
                SET title = %s, tag = %s, color = %s, sort_order = %s,
                    is_archived = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                RETURNING id, title, tag, color, sort_order, is_archived, created_at, updated_at
                """,
                (title, tag, color, sort_order, is_archived, habit_id, user_id),
            )
            row = await cur.fetchone()
            since = date.today() - timedelta(days=60)
            await cur.execute(
                """
                SELECT day FROM site_user_habit_checks
                WHERE habit_id = %s AND day >= %s
                ORDER BY day DESC
                """,
                (habit_id, since),
            )
            check_rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    days = [
        (r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])[:10]) for r in check_rows
    ]
    day_objs = [
        r[0] if hasattr(r[0], "isoformat") else date.fromisoformat(str(r[0])[:10])
        for r in check_rows
    ]
    return _habit_payload(row, checks=days, streak=habit_streak(day_objs))


@router.delete("/habits/{habit_id}")
async def delete_habit(
    habit_id: int,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if habit_id <= 0:
        raise HTTPException(status_code=400, detail="invalid habit id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_user_habits
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (habit_id, user["user_id"]),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="habit not found")
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "id": int(row[0])}


@router.post("/habits/{habit_id}/checks")
async def set_habit_check(
    habit_id: int,
    body: HabitCheckIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    from services.task_planner import habit_streak

    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if habit_id <= 0:
        raise HTTPException(status_code=400, detail="invalid habit id")
    day_value = date.today()
    if body.day is not None and body.day.strip():
        day_value = _parse_optional_due_date(body.day) or date.today()
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM site_user_habits
                WHERE id = %s AND user_id = %s
                """,
                (habit_id, user_id),
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="habit not found")
            if body.checked:
                await cur.execute(
                    """
                    INSERT INTO site_user_habit_checks (habit_id, day)
                    VALUES (%s, %s)
                    ON CONFLICT (habit_id, day) DO NOTHING
                    """,
                    (habit_id, day_value),
                )
            else:
                await cur.execute(
                    """
                    DELETE FROM site_user_habit_checks
                    WHERE habit_id = %s AND day = %s
                    """,
                    (habit_id, day_value),
                )
            since = date.today() - timedelta(days=60)
            await cur.execute(
                """
                SELECT day FROM site_user_habit_checks
                WHERE habit_id = %s AND day >= %s
                ORDER BY day DESC
                """,
                (habit_id, since),
            )
            check_rows = await cur.fetchall()
            await cur.execute(
                """
                SELECT id, title, tag, color, sort_order, is_archived, created_at, updated_at
                FROM site_user_habits WHERE id = %s
                """,
                (habit_id,),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    days = [
        (r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])[:10]) for r in check_rows
    ]
    day_objs = [
        r[0] if hasattr(r[0], "isoformat") else date.fromisoformat(str(r[0])[:10])
        for r in check_rows
    ]
    return _habit_payload(row, checks=days, streak=habit_streak(day_objs))


def _note_file_payload(row: Any) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "filename": str(row[1] or ""),
        "contentType": str(row[2] or ""),
        "sizeBytes": int(row[3] or 0),
        "createdAt": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
    }


def _note_payload(row: Any, *, files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "title": str(row[1] or ""),
        "body": str(row[2] or ""),
        "tag": str(row[3] or ""),
        "createdAt": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
        "updatedAt": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
        "files": files or [],
    }


@router.get("/notes")
async def list_notes(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, title, body, tag, created_at, updated_at
                FROM site_user_notes
                WHERE user_id = %s
                ORDER BY updated_at DESC, id DESC
                """,
                (user_id,),
            )
            notes = await cur.fetchall()
            result: list[dict[str, Any]] = []
            for note in notes:
                await cur.execute(
                    """
                    SELECT id, filename, content_type, size_bytes, created_at
                    FROM site_user_note_files
                    WHERE note_id = %s
                    ORDER BY id ASC
                    """,
                    (int(note[0]),),
                )
                files = [_note_file_payload(f) for f in await cur.fetchall()]
                result.append(_note_payload(note, files=files))
    finally:
        await release_site_db_connection(conn)
    return {"items": result}


@router.post("/notes")
async def create_note(
    body: NoteCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    title = (body.title or "").strip()[:512] or "Без названия"
    body_text = (body.body or "")[:100_000]
    tag = (body.tag or "").strip()[:64]
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_user_notes (user_id, title, body, tag)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, body, tag, created_at, updated_at
                """,
                (user["user_id"], title, body_text, tag),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return _note_payload(row, files=[])


@router.patch("/notes/{note_id}")
async def update_note(
    note_id: int,
    body: NoteUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if note_id <= 0:
        raise HTTPException(status_code=400, detail="invalid note id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, title, body, tag, created_at, updated_at
                FROM site_user_notes
                WHERE id = %s AND user_id = %s
                """,
                (note_id, user_id),
            )
            existing = await cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="note not found")
            title = str(existing[1] or "")
            body_text = str(existing[2] or "")
            tag = str(existing[3] or "")
            if body.title is not None:
                title = body.title.strip()[:512] or "Без названия"
            if body.body is not None:
                body_text = body.body[:100_000]
            if body.tag is not None:
                tag = body.tag.strip()[:64]
            await cur.execute(
                """
                UPDATE site_user_notes
                SET title = %s, body = %s, tag = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                RETURNING id, title, body, tag, created_at, updated_at
                """,
                (title, body_text, tag, note_id, user_id),
            )
            row = await cur.fetchone()
            await cur.execute(
                """
                SELECT id, filename, content_type, size_bytes, created_at
                FROM site_user_note_files
                WHERE note_id = %s
                ORDER BY id ASC
                """,
                (note_id,),
            )
            files = [_note_file_payload(f) for f in await cur.fetchall()]
    finally:
        await release_site_db_connection(conn)
    return _note_payload(row, files=files)


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    if note_id <= 0:
        raise HTTPException(status_code=400, detail="invalid note id")
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_user_notes
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (note_id, user["user_id"]),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="note not found")
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "id": int(row[0])}


@router.post("/notes/{note_id}/files")
async def upload_note_file(
    note_id: int,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    if note_id <= 0:
        raise HTTPException(status_code=400, detail="invalid note id")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_NOTE_FILE_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed formats: {', '.join(sorted(ALLOWED_NOTE_FILE_EXT))}",
        )
    raw = await read_upload_limited(file, max_bytes=MAX_NOTE_FILE_BYTES, label="Note file")
    safe_name = Path(file.filename).name[:200]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    content_type = NOTE_MIME_BY_EXT.get(ext, "application/octet-stream")
    key = f"{S3_SITE_NOTES_PREFIX}/{user_id}/{note_id}/{stored_name}"
    storage = get_storage()
    if storage:
        await storage.put(key, raw, content_type=content_type)
        storage_key = key
    else:
        target_dir = UPLOADS_SITE_NOTES_DIR / str(user_id) / str(note_id)
        await async_fs.makedirs(target_dir)
        await async_fs.write_bytes(target_dir / stored_name, raw)
        storage_key = f"local:{user_id}/{note_id}/{stored_name}"

    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM site_user_notes
                WHERE id = %s AND user_id = %s
                """,
                (note_id, user_id),
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="note not found")
            await cur.execute(
                """
                INSERT INTO site_user_note_files
                    (note_id, user_id, filename, content_type, size_bytes, storage_key)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, filename, content_type, size_bytes, created_at
                """,
                (note_id, user_id, safe_name, content_type, len(raw), storage_key),
            )
            row = await cur.fetchone()
            await cur.execute(
                """
                UPDATE site_user_notes SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (note_id,),
            )
    finally:
        await release_site_db_connection(conn)
    return _note_file_payload(row)


@router.get("/notes/{note_id}/files/{file_id}")
async def download_note_file(
    note_id: int,
    file_id: int,
    authorization: Optional[str] = Header(None),
) -> Response:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT filename, content_type, storage_key
                FROM site_user_note_files
                WHERE id = %s AND note_id = %s AND user_id = %s
                """,
                (file_id, note_id, user_id),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="file not found")
    filename = str(row[0] or "file")
    content_type = str(row[1] or "application/octet-stream")
    storage_key = str(row[2] or "")
    if storage_key.startswith("local:"):
        rel = storage_key[len("local:") :]
        if ".." in rel or rel.startswith("/") or "\\" in rel:
            raise HTTPException(status_code=400, detail="Invalid storage key")
        path = UPLOADS_SITE_NOTES_DIR / rel
        if not path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        data = path.read_bytes()
    else:
        storage = get_storage()
        if not storage:
            raise HTTPException(status_code=404, detail="storage unavailable")
        data = await storage.get_bytes(storage_key)
        if not data:
            raise HTTPException(status_code=404, detail="file not found")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type=content_type, headers=headers)


@router.delete("/notes/{note_id}/files/{file_id}")
async def delete_note_file(
    note_id: int,
    file_id: int,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_user_note_files
                WHERE id = %s AND note_id = %s AND user_id = %s
                RETURNING id
                """,
                (file_id, note_id, user_id),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="file not found")
    finally:
        await release_site_db_connection(conn)
    return {"ok": True, "id": int(row[0])}


@router.get("/focus-logs")
async def list_focus_logs(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, minutes, label, created_at
                FROM site_user_focus_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (user["user_id"],),
            )
            rows = await cur.fetchall()
    finally:
        await release_site_db_connection(conn)
    return {
        "items": [
            {
                "id": int(r[0]),
                "minutes": int(r[1]),
                "label": str(r[2] or ""),
                "createdAt": r[3].isoformat() if hasattr(r[3], "isoformat") else str(r[3]),
            }
            for r in rows
        ]
    }


@router.post("/focus-logs")
async def create_focus_log(
    body: FocusLogCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await _require_user(authorization)
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_user_focus_logs (user_id, minutes, label)
                VALUES (%s, %s, %s)
                RETURNING id, minutes, label, created_at
                """,
                (user["user_id"], int(body.minutes), (body.label or "").strip()[:128]),
            )
            row = await cur.fetchone()
    finally:
        await release_site_db_connection(conn)
    return {
        "id": int(row[0]),
        "minutes": int(row[1]),
        "label": str(row[2] or ""),
        "createdAt": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
    }

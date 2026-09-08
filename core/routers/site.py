"""9to18.ru site contour: auth, apps, blogs, contacts.

Роли:
- user — чтение опубликованных страниц и статей всех сервисов
- админ сервиса (site_app_admins) — плашка, страница и блог своих сервисов
- супер-админ (site_users.site_role = site_admin) — всё выше + любой сервис,
  спотлайт, назначение админов сервисов
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets as py_secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from config import settings
from site_database import get_site_db_connection, release_site_db_connection

router = APIRouter(prefix="/site", tags=["Site9to18"])

SITE_AUD = "9to18"
SITE_PROMO_KEY = "site_9to18_promo"
SITE_LEARNING_MAP_KEY = "site_9to18_learning_map"
LEARNING_MAP_MAX_CHARS = 1_500_000
ACCESS_MINUTES = 60 * 12
ALGORITHM = "HS256"

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
        "subtitle": "Теория, лабы, шпаргалки",
        "description": "Учебные материалы по сборке сервисов.",
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
        "slug": "e2e-tester",
        "title": "E2E Tester",
        "subtitle": "Локально · Playwright",
        "description": (
            "Локальный Docker-сервис E2E на 127.0.0.1:8300: YAML/JSON/Playwright, "
            "креды и отчёты. Без облачной панели."
        ),
        "accent": "#f43f5e",
        "emoji": "🧪",
        "external_href": "http://127.0.0.1:8300",
        "sort_order": 4,
    },
    {
        "slug": "menu",
        "title": "Menu",
        "subtitle": "Каталог и корзина",
        "description": "Каталог материалов и позиций с корзиной.",
        "accent": "#fbbf24",
        "emoji": "📋",
        "sort_order": 5,
    },
    {
        "slug": "rating",
        "title": "Rating",
        "subtitle": "Таблица лидеров",
        "description": "Рейтинг участников по играм и тестам.",
        "accent": "#a78bfa",
        "emoji": "🏆",
        "sort_order": 6,
    },
    {
        "slug": "events",
        "title": "Events",
        "subtitle": "Мероприятия",
        "description": "Календарь стримов, воркшопов и встреч.",
        "accent": "#f472b6",
        "emoji": "📅",
        "sort_order": 7,
    },
    {
        "slug": "copyparse",
        "title": "CopyParse",
        "subtitle": "SaaS · copyparse.ru",
        "description": "Платформа кросспостинга и SMM — живой стенд курса.",
        "accent": "#fb923c",
        "emoji": "🚀",
        "external_href": "https://www.copyparse.ru",
        "sort_order": 8,
    },
    {
        "slug": "profile",
        "title": "Profile",
        "subtitle": "Личный кабинет",
        "description": "Прогресс Learn, настройки и доступы.",
        "accent": "#38bdf8",
        "emoji": "👤",
        "app_path": "/account",
        "sort_order": 9,
    },
    {
        "slug": "help",
        "title": "Help",
        "subtitle": "Помощь и FAQ",
        "description": "Справка по платформе и разделам.",
        "accent": "#94a3b8",
        "emoji": "💬",
        "sort_order": 10,
    },
    {
        "slug": "tasks",
        "title": "Tasks",
        "subtitle": "Чек-лист Learn",
        "description": "Личные задачи и прогресс по выпускам Learn.",
        "accent": "#4ade80",
        "emoji": "✅",
        "app_path": "/game/tasks",
        "sort_order": 11,
    },
    {
        "slug": "chat",
        "title": "Chat",
        "subtitle": "Чат группы",
        "description": "Вопросы и общение учебной группы.",
        "accent": "#22d3ee",
        "emoji": "💭",
        "sort_order": 12,
    },
    {
        "slug": "cert",
        "title": "Cert",
        "subtitle": "Сертификаты",
        "description": "Сертификат о прохождении сезона Learn.",
        "accent": "#eab308",
        "emoji": "🎓",
        "app_path": "/game/cert",
        "sort_order": 13,
    },
    {
        "slug": "stream",
        "title": "Stream",
        "subtitle": "Стримы и эфиры",
        "description": "Прямые эфиры и записи разборов.",
        "accent": "#ef4444",
        "emoji": "📺",
        "sort_order": 14,
    },
    {
        "slug": "news",
        "title": "News",
        "subtitle": "Новости",
        "description": "Анонсы выпусков и обновлений.",
        "accent": "#818cf8",
        "emoji": "📰",
        "sort_order": 15,
    },
    {
        "slug": "forum",
        "title": "Forum",
        "subtitle": "Форум",
        "description": "Разборы ошибок и обмен опытом.",
        "accent": "#c084fc",
        "emoji": "🗣️",
        "sort_order": 16,
    },
    {
        "slug": "code",
        "title": "Code",
        "subtitle": "Редактор кода",
        "description": "Короткие упражнения в браузере.",
        "accent": "#2dd4bf",
        "emoji": "⌨️",
        "sort_order": 17,
    },
    {
        "slug": "map",
        "title": "Map",
        "subtitle": "Карта курса",
        "description": "Сезоны, выпуски и связи тем.",
        "accent": "#14b8a6",
        "emoji": "🗺️",
        "sort_order": 18,
    },
    {
        "slug": "team",
        "title": "Team",
        "subtitle": "Команды",
        "description": "Совместные проекты и парное обучение.",
        "accent": "#f97316",
        "emoji": "👥",
        "sort_order": 19,
    },
    {
        "slug": "quiz",
        "title": "Quiz",
        "subtitle": "Закрепление теории",
        "description": "Короткие вопросы по выпускам Learn.",
        "accent": "#f59e0b",
        "emoji": "🧠",
        "app_path": "/game/quiz",
        "sort_order": 20,
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
            if count_row and int(count_row[0] or 0) > 0:
                await _upsert_featured_apps(cur)
                return
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
                stub_slug = "about"
                stub_title = f"О приложении {app['title']}"
                stub_body = (
                    f"Это заглушка блога приложения **{app['title']}**.\n\n"
                    f"{app.get('description', '')}\n\n"
                    "Скоро здесь появятся новости о развитии сервиса. "
                    "Пользователи 9to18 могут читать блоги приложений и "
                    "писать разработчикам через форму обратной связи."
                )
                await cur.execute(
                    """
                    INSERT INTO site_posts (app_slug, slug, title, body, is_published)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (app_slug, slug) DO NOTHING
                    """,
                    (app["slug"], stub_slug, stub_title, stub_body),
                )
            await _upsert_featured_apps(cur)
    finally:
        await release_site_db_connection(conn)


async def _upsert_featured_apps(cur: Any) -> None:
    """Синхронизация «живых» сервисов на уже заполненной БД (без полного ресида)."""
    featured_slugs = {
        "e2e-tester",
        "copyparse",
        "learning-map",
        "learn",
        "bowl",
        "profile",
        "tasks",
        "cert",
        "quiz",
    }
    stub_hide_slugs = {
        "menu",
        "rating",
        "events",
        "help",
        "chat",
        "stream",
        "news",
        "forum",
        "code",
        "map",
        "team",
    }
    featured = [app for app in DEFAULT_APPS if app["slug"] in featured_slugs]
    for app in featured:
        await cur.execute(
            """
            INSERT INTO site_apps (
                slug, title, subtitle, description, accent, emoji,
                external_href, app_path, is_visible, sort_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
            ON CONFLICT (slug) DO UPDATE SET
                title = EXCLUDED.title,
                subtitle = EXCLUDED.subtitle,
                description = EXCLUDED.description,
                accent = EXCLUDED.accent,
                emoji = EXCLUDED.emoji,
                external_href = EXCLUDED.external_href,
                app_path = COALESCE(NULLIF(EXCLUDED.app_path, ''), site_apps.app_path),
                is_visible = TRUE,
                -- sort_order не трогаем: его задаёт супер-админ через /admin/apps/reorder
                updated_at = CURRENT_TIMESTAMP
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
        stub_body = (
            f"**{app['title']}** — {app.get('description', '')}\n\n"
            "Откройте плитку на главной 9to18, читайте блог и пишите разработчикам."
        )
        if app["slug"] == "e2e-tester":
            stub_body = (
                "## E2E Tester (только локально)\n\n"
                "Браузерные E2E на Playwright в **одном Docker-контейнере** с SQLite. "
                "Облачной панели нет: панель слушает `127.0.0.1:8300` на вашей машине.\n\n"
                "### Запуск\n\n"
                "```bash\n"
                "cp deploy/e2e-tester/.env.example deploy/e2e-tester/.env\n"
                "# задайте TESTER_SECRET_KEY (Fernet)\n"
                "docker compose -f deploy/e2e-tester/docker-compose.yml "
                "--env-file deploy/e2e-tester/.env up -d --build\n"
                "# или: python deploy/scripts/compose_up_sequential.py --with e2e --build\n"
                "```\n\n"
                "Панель: [http://127.0.0.1:8300](http://127.0.0.1:8300)\n\n"
                "Для 9to18 задайте `TARGET_UI_URL=http://host.docker.internal:8200` "
                "(или публичный URL) и загрузите `examples/nine_to_eighteen_smoke.yaml`.\n"
            )
        await cur.execute(
            """
            INSERT INTO site_posts (app_slug, slug, title, body, is_published)
            VALUES (%s, 'about', %s, %s, TRUE)
            ON CONFLICT (app_slug, slug) DO UPDATE SET
                title = EXCLUDED.title,
                body = EXCLUDED.body,
                updated_at = CURRENT_TIMESTAMP
            """,
            (app["slug"], f"О приложении {app['title']}", stub_body),
        )
    # Скрываем заглушки (не трогаем featured).
    if stub_hide_slugs:
        await cur.execute(
            """
            UPDATE site_apps
            SET is_visible = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE slug = ANY(%s::text[]) AND is_visible = TRUE
            """,
            (list(stub_hide_slugs),),
        )


@router.on_event("startup")
async def _startup_seed() -> None:
    try:
        await ensure_site_seeded()
    except Exception:
        # Table may not exist until patch is applied.
        pass


@router.post("/auth/register")
async def register(body: RegisterIn) -> dict[str, Any]:
    await ensure_site_seeded()
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
async def login(body: LoginIn) -> dict[str, Any]:
    await ensure_site_seeded()
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
    return {
        "id": user["user_id"],
        "email": user.get("email") or "",
        "username": user["username"],
        "siteRole": user["site_role"],
        "appAdmin": user["app_admin"],
    }


@router.get("/apps")
async def list_apps() -> dict[str, Any]:
    await ensure_site_seeded()
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
    try:
        await ensure_site_seeded()
    except Exception:
        # Не блокируем список, если сид/hide упал (например, нет колонок).
        pass
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
            stub_title = f"О приложении {body.title.strip()}"
            stub_body = (
                f"**{body.title.strip()}** — {body.description or body.subtitle}\n\n"
                "Скоро здесь появятся новости о развитии сервиса."
            )
            await cur.execute(
                """
                INSERT INTO site_posts (app_slug, slug, title, body, is_published)
                VALUES (%s, 'about', %s, %s, TRUE)
                ON CONFLICT (app_slug, slug) DO NOTHING
                """,
                (slug, stub_title, stub_body),
            )
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
    await ensure_site_seeded()
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
    await ensure_site_seeded()
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
async def submit_contact(body: ContactIn) -> dict[str, Any]:
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
                "href": f"/app/{app_slug}/{post_slug}",
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
    await ensure_site_seeded()
    safe_limit = max(1, min(int(limit or 5), 20))
    items = await _spotlight_items(limit=safe_limit, curated_keys=None)
    return {"items": items}


@router.get("/promo")
async def get_promo() -> dict[str, Any]:
    """Спотлайт: настройки + до 5 карточек (ручной curatedKeys или авто по дате)."""
    await ensure_site_seeded()
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
    await ensure_site_seeded()
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
                SELECT id, email, username, site_role, is_active, created_at
                FROM site_users
                ORDER BY id ASC
                LIMIT 500
                """
            )
            rows = await cur.fetchall()
            users: list[dict[str, Any]] = []
            for row in rows:
                uid = int(row[0])
                await cur.execute(
                    "SELECT app_slug FROM site_app_admins WHERE user_id = %s ORDER BY app_slug",
                    (uid,),
                )
                apps = [str(r[0]) for r in await cur.fetchall()]
                users.append(
                    {
                        "id": uid,
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
    if body.site_role is None and body.is_active is None and body.password is None:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if actor["user_id"] == user_id and body.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    if actor["user_id"] == user_id and body.site_role == "user":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

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


@router.post("/auth/forgot-password")
async def forgot_password(body: PasswordForgotIn) -> dict[str, Any]:
    """Создаёт reset-токен. В dev возвращает token в ответе (без SMTP)."""
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
    # Всегда одинаковый ответ снаружи (кроме dev-токена когда пользователь найден)
    result: dict[str, Any] = {
        "ok": True,
        "detail": "Если аккаунт существует, токен сброса выдан (SMTP пока не подключён).",
    }
    if token:
        result["resetToken"] = token
    return result


@router.post("/auth/reset-password")
async def reset_password(body: PasswordResetIn) -> dict[str, Any]:
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

    return {
        "quiz": {
            "attempts": quiz_attempts,
            "scoreSum": quiz_score_sum,
            "totalSum": quiz_total_sum,
            "avgPercent": round((quiz_score_sum / quiz_total_sum) * 100) if quiz_total_sum else 0,
            "lastAt": last_quiz_at,
            "recent": [
                {
                    "sourceKey": str(row[0]),
                    "score": int(row[1] or 0),
                    "total": int(row[2] or 0),
                    "finishedAt": row[3].isoformat()
                    if hasattr(row[3], "isoformat")
                    else str(row[3]),
                }
                for row in recent_quiz
            ],
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

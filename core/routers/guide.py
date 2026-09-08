"""Публичная справка (/about): блоки контента с настраиваемым стилем."""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from database import get_db_connection, release_db_connection

router = APIRouter(prefix="/guide", tags=["Guide"])

DEFAULT_STYLE: dict[str, Any] = {
    "titleColor": "",
    "subtitleColor": "",
    "textColor": "",
    "backgroundColor": "",
    "borderColor": "",
    "borderRadius": "12px",
    "padding": "",
    "titleFontSize": "",
    "bodyFontSize": "14px",
    "titleFontWeight": "600",
}

# Seed matches previous hardcoded About sections (markdown body).
DEFAULT_BLOCKS: list[dict[str, Any]] = [
    {
        "slug": "intro",
        "toc_label": "Вступление",
        "title": "Справка по сервису",
        "subtitle": (
            "Описание Control Panel: как начать, что умеет платформа, "
            "тарифы Free / Standard / Full, роли в команде."
        ),
        "body": "",
        "sort_order": 0,
        "style": {**DEFAULT_STYLE},
    },
    {
        "slug": "overview",
        "toc_label": "О сервисе",
        "title": "О сервисе",
        "subtitle": "Единая панель для контента в Telegram, VK и других сетях",
        "body": (
            "**Control Panel** — платформа для SMM-операций: бренды и каналы, единый инбокс, "
            "мультипостинг с адаптацией под сеть, календарь публикаций, аналитика send/receive "
            "и командные роли.\n\n"
            "Авторизация и секреты остаются в силосах сетей (Telegram, VKontakte и др.). "
            "Операционка — в общих разделах Brands, Channels, Inbox, Posts, Calendar, Analytics.\n\n"
            "- Публикация и сбор контента (TG, VK, Threads, Twitter, WordPress, URL и др.)\n"
            "- Мульти-send в own-каналы бренда с расписанием и квотами по тарифу\n"
            "- Инбокс: чтение, правка, reply и redirect/repost\n"
            "- Команды (группы) с ролями Admin / Editor / Analyst"
        ),
        "sort_order": 10,
        "style": {**DEFAULT_STYLE},
    },
    {
        "slug": "howto",
        "toc_label": "Как пользоваться",
        "title": "Краткая инструкция",
        "subtitle": "Типовой сценарий за 5 шагов",
        "body": (
            "1. **Регистрация и тариф.** Создайте аккаунт, при необходимости смените тариф в "
            "Profile → Billing или попросите администратора.\n"
            "2. **Подключите сети.** В разделах Telegram / VKontakte выполните Auth и укажите "
            "каналы/группы для публикации и сбора.\n"
            "3. **Соберите бренд и каналы.** В Brands создайте бренд. В Channels добавьте "
            "own / source / competitor, включите publish и collect.\n"
            "4. **Публикуйте.** В Posts напишите текст, выберите own-каналы, при желании "
            "Adapt TG/VK, отправьте сейчас или в Calendar. На Standard+ можно включить approval.\n"
            "5. **Работайте с входящими.** Inbox показывает собранные сообщения. Редактируйте "
            "текст, отвечайте или делайте redirect (Standard+). Смотрите send/receive в Analytics."
        ),
        "sort_order": 20,
        "style": {**DEFAULT_STYLE},
    },
    {
        "slug": "features",
        "toc_label": "Возможности",
        "title": "Возможности",
        "subtitle": "Основные модули продукта",
        "body": (
            "### Channels hub\n"
            "Единый список каналов TG/VK с ролями own/source/competitor и флагами publish/collect.\n\n"
            "### Composer & multi-send\n"
            "Один текст → несколько каналов, адаптеры сетей, CSV-импорт, AI summarize/rewrite/adapt.\n\n"
            "### Calendar\n"
            "Контент-план: неделя/месяц, drag-and-drop по слотам, рубрики (повторяющийся контент),\n"
            "best times (Standard+), очередь pending approval. Горизонт Free 7 / Standard 30 / Full 90 дней.\n\n"
            "### Inbox\n"
            "Входящие из коллекторов, edit перед репостом, reply и redirect в own-каналы.\n\n"
            "### Analytics\n"
            "Overview ER/reach и таблица send / receive / failed по каналам за период тарифа.\n\n"
            "### Automations\n"
            "Правила RSS / tg_repost / mention в рамках лимита тарифа (Standard+).\n\n"
            "### Team\n"
            "Группы пользователей, приглашения по email, роли Admin / Editor / Analyst.\n\n"
            "### Силосы сетей\n"
            "Отдельные экраны Auth и глубоких настроек без смешивания с операционкой SMM."
        ),
        "sort_order": 30,
        "style": {**DEFAULT_STYLE},
    },
    {
        "slug": "tariffs",
        "toc_label": "Тарифы",
        "title": "Тарифы",
        "subtitle": "Free · Standard · Full — лимиты проверяются на API",
        "body": (
            "### Free\n"
            "Старт для соло: один бренд, чтение инбокса без reply.\n"
            "- Own-каналы: 3 · Бренды: 1 · Посты/мес: 300 · Storage: 1 GB · Team: 1\n"
            "- Целей/job: 1 · Расписание: 7 дней · Рубрики: 1 · Статистика: 7 дней\n"
            "- Inbox read: да · Reply/redirect: нет · AI: нет · Competitors: нет\n\n"
            "### Standard\n"
            "Команда и операционка: multi-send, reply, AI, automations.\n"
            "- Own-каналы: 10 · Бренды: 5 · Посты/мес: 3 000 · Storage: 10 GB · Team: 5\n"
            "- Целей/job: 5 · Расписание: 30 дней · Рубрики: 10 · AI: 100/мес · Automations: 5 · Статистика: 90 дней\n"
            "- Reply/redirect, AI, approval, best times: да · Competitors: нет\n\n"
            "### Full\n"
            "Максимум каналов, competitors, webhooks и SLA.\n"
            "- Own-каналы: 20 · Бренды: 20 · Посты/мес: 50 000 · Storage: 100 GB · Team: 20\n"
            "- Целей/job: 20 · Расписание: 90 дней · Рубрики: 50 · AI: 2 000/мес · Automations: 50 · Статистика: 365 дней\n"
            "- Competitors, webhooks, priority queue, SLA: да\n\n"
            "Смена тарифа: Profile → Billing или через администратора платформы."
        ),
        "sort_order": 40,
        "style": {**DEFAULT_STYLE},
    },
    {
        "slug": "roles",
        "toc_label": "Роли и группы",
        "title": "Роли и группы",
        "subtitle": "Глобальная роль аккаунта и роль внутри команды (Team)",
        "body": (
            "### Глобальные роли\n"
            "- **user** — владелец аккаунта: бренды, каналы, посты в рамках тарифа.\n"
            "- **admin** — администратор платформы: Administration, Polls, Checks, назначение тарифов.\n\n"
            "### Группы (Team)\n"
            "Команда объединяет несколько аккаунтов. Число мест ограничено тарифом (1 / 5 / 20).\n\n"
            "- **Admin** — участники, настройки, публикация, approval, полный доступ.\n"
            "- **Editor** — посты, инбокс (по тарифу), календарь; может отправлять на approval.\n"
            "- **Analyst** — просмотр аналитики без права публикации и изменения каналов.\n\n"
            "Алиасы: manager → Admin, author → Editor."
        ),
        "sort_order": 50,
        "style": {**DEFAULT_STYLE},
    },
]


class GuideBlockStyle(BaseModel):
    titleColor: Optional[str] = None
    subtitleColor: Optional[str] = None
    textColor: Optional[str] = None
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    borderRadius: Optional[str] = None
    padding: Optional[str] = None
    titleFontSize: Optional[str] = None
    bodyFontSize: Optional[str] = None
    titleFontWeight: Optional[str] = None


class GuideBlockOut(BaseModel):
    id: int
    slug: str
    toc_label: str
    title: str
    subtitle: str
    body: str
    sort_order: int
    is_visible: bool
    style: dict[str, Any] = Field(default_factory=dict)


class GuideBlockUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=64)
    toc_label: Optional[str] = Field(None, max_length=128)
    title: Optional[str] = Field(None, max_length=255)
    subtitle: Optional[str] = None
    body: Optional[str] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None
    style: Optional[dict[str, Any]] = None


class GuideBlockCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    toc_label: str = Field("", max_length=128)
    title: str = Field("", max_length=255)
    subtitle: str = ""
    body: str = ""
    sort_order: int = 100
    is_visible: bool = True
    style: dict[str, Any] = Field(default_factory=dict)


def _require_admin(x_user_id: Optional[str], x_user_role: Optional[str]) -> None:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage guide blocks")


def _row_to_block(row: tuple) -> dict[str, Any]:
    style = row[8] if isinstance(row[8], dict) else (json.loads(row[8]) if row[8] else {})
    return {
        "id": row[0],
        "slug": row[1],
        "toc_label": row[2] or "",
        "title": row[3] or "",
        "subtitle": row[4] or "",
        "body": row[5] or "",
        "sort_order": int(row[6] or 0),
        "is_visible": bool(row[7]),
        "style": style or {},
    }


async def _count_blocks(cur) -> int:
    await cur.execute("SELECT COUNT(*) FROM guide_blocks")
    row = await cur.fetchone()
    return int(row[0] if row else 0)


async def _seed_defaults(cur) -> None:
    for b in DEFAULT_BLOCKS:
        await cur.execute(
            """
            INSERT INTO guide_blocks
                (slug, toc_label, title, subtitle, body, sort_order, is_visible, style)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s::jsonb)
            ON CONFLICT (slug) DO NOTHING
            """,
            (
                b["slug"],
                b["toc_label"],
                b["title"],
                b["subtitle"],
                b["body"],
                b["sort_order"],
                json.dumps(b.get("style") or DEFAULT_STYLE),
            ),
        )


async def _list_blocks(*, visible_only: bool) -> list[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            if await _count_blocks(cur) == 0:
                await _seed_defaults(cur)
            if visible_only:
                await cur.execute(
                    """
                    SELECT id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style
                    FROM guide_blocks
                    WHERE is_visible = TRUE
                    ORDER BY sort_order ASC, id ASC
                    """
                )
            else:
                await cur.execute(
                    """
                    SELECT id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style
                    FROM guide_blocks
                    ORDER BY sort_order ASC, id ASC
                    """
                )
            rows = await cur.fetchall()
            return [_row_to_block(r) for r in rows]
    finally:
        await release_db_connection(conn)


@router.get("/blocks")
async def list_public_blocks() -> dict[str, Any]:
    """Публичный список видимых блоков справки (без JWT)."""
    return {"blocks": await _list_blocks(visible_only=True)}


@router.get("/blocks/admin")
async def list_admin_blocks(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_admin(x_user_id, x_user_role)
    return {"blocks": await _list_blocks(visible_only=False)}


@router.post("/blocks")
async def create_block(
    body: GuideBlockCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_admin(x_user_id, x_user_role)
    slug = body.slug.strip().lower().replace(" ", "-")
    style = {**DEFAULT_STYLE, **(body.style or {})}
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """
                    INSERT INTO guide_blocks
                        (slug, toc_label, title, subtitle, body, sort_order, is_visible, style)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style
                    """,
                    (
                        slug,
                        body.toc_label,
                        body.title,
                        body.subtitle,
                        body.body,
                        body.sort_order,
                        body.is_visible,
                        json.dumps(style),
                    ),
                )
            except Exception as exc:
                if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                    raise HTTPException(status_code=400, detail="slug already exists") from exc
                raise
            row = await cur.fetchone()
            return _row_to_block(row)
    finally:
        await release_db_connection(conn)


@router.patch("/blocks/{block_id}")
async def update_block(
    block_id: int,
    body: GuideBlockUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_admin(x_user_id, x_user_role)
    fields: list[str] = []
    params: list[Any] = []
    data = body.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] is not None:
        data["slug"] = str(data["slug"]).strip().lower().replace(" ", "-")
    if "style" in data and data["style"] is not None:
        fields.append("style = %s::jsonb")
        params.append(json.dumps(data.pop("style")))
    for key in ("slug", "toc_label", "title", "subtitle", "body", "sort_order", "is_visible"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = %s")
            params.append(data[key])
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(block_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE guide_blocks SET {', '.join(fields)}
                WHERE id = %s
                RETURNING id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style
                """,
                params,
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Block not found")
            return _row_to_block(row)
    finally:
        await release_db_connection(conn)


@router.delete("/blocks/{block_id}")
async def delete_block(
    block_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    _require_admin(x_user_id, x_user_role)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM guide_blocks WHERE id = %s RETURNING id",
                (block_id,),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Block not found")
            return {"ok": True, "id": block_id}
    finally:
        await release_db_connection(conn)


@router.post("/blocks/seed")
async def reseeds_blocks(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    """Восстановить дефолтные блоки (только отсутствующие slug; не затирает правки)."""
    _require_admin(x_user_id, x_user_role)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await _seed_defaults(cur)
        return {"blocks": await _list_blocks(visible_only=False)}
    finally:
        await release_db_connection(conn)

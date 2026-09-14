"""Learn posts service (9to18 blog/course mirror)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from database import get_db_connection, release_db_connection

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "learn_seed.json"

POST_COLUMNS = (
    "id, slug, episode, title, short_title, rubric_id, sort_order, "
    "theory, lab, cheatsheet, diagram, links, structured, "
    "theory_format, lab_format, cheatsheet_format, "
    "profiles, level, tags, excerpt, duration_min, prerequisites, "
    "author, author_url, cover_url, seo_title, seo_description, "
    "seo_keywords, canonical_url, "
    "published_at, updated_at, created_at"
)

VALID_FORMATS = ("markdown", "html")
VALID_RUBRICS = ("architecture", "api", "data", "frontend", "tools")
VALID_PROFILES = ("analyst", "devops", "developer", "tester", "product_owner")
VALID_LEVELS = ("intern", "junior", "middle", "senior", "lead")


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _normalize_format(value: Any, default: str = "markdown") -> str:
    raw = str(value or default).strip().lower()
    return raw if raw in VALID_FORMATS else default


def _parse_json_list(raw: Any) -> list[Any]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(raw, list):
        return []
    return raw


def _normalize_links(raw: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in _parse_json_list(raw):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()[:255]
        href = str(item.get("href") or "").strip()[:1024]
        if label or href:
            out.append({"label": label or href, "href": href or "#"})
    return out


def _normalize_string_list(
    raw: Any, *, max_item_len: int = 64, max_items: int = 32
) -> list[str]:
    if isinstance(raw, str) and raw.strip():
        items = [part.strip() for part in raw.replace(";", ",").split(",")]
    else:
        items = []
        for item in _parse_json_list(raw):
            items.append(str(item or "").strip())
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = item[:max_item_len]
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
        if len(out) >= max_items:
            break
    return out


def _normalize_profiles(raw: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _normalize_string_list(raw, max_item_len=32, max_items=16):
        value = item.lower()
        if value not in VALID_PROFILES or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _normalize_level(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    return value if value in VALID_LEVELS else ""


def _normalize_prerequisites(raw: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _normalize_string_list(raw, max_item_len=128, max_items=24):
        slug = item.lower().replace(" ", "-")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def _normalize_structured(raw: Any) -> Optional[dict[str, Any]]:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            raw = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
    if not isinstance(raw, dict) or not raw:
        return None
    version = raw.get("version")
    if version not in (1, "1"):
        return None
    anki = raw.get("anki")
    if not isinstance(anki, list) or not any(
        isinstance(item, dict)
        and str(item.get("front") or "").strip()
        and str(item.get("back") or "").strip()
        for item in anki
    ):
        return None
    return raw


def _row_post(row: tuple) -> dict[str, Any]:
    structured = _normalize_structured(row[12])
    return {
        "id": row[0],
        "slug": row[1],
        "episode": row[2] or "",
        "title": row[3] or "",
        "shortTitle": row[4] or "",
        "rubricId": row[5] or "architecture",
        "order": int(row[6] or 0),
        "theory": row[7] or "",
        "lab": row[8] or "",
        "cheatsheet": row[9] or "",
        "diagram": row[10] or "",
        "links": _normalize_links(row[11]),
        "structured": structured,
        "theoryFormat": _normalize_format(row[13]),
        "labFormat": _normalize_format(row[14]),
        "cheatsheetFormat": _normalize_format(row[15]),
        "profiles": _normalize_profiles(row[16]),
        "level": _normalize_level(row[17]),
        "tags": _normalize_string_list(row[18]),
        "excerpt": row[19] or "",
        "durationMin": int(row[20] or 0),
        "prerequisites": _normalize_prerequisites(row[21]),
        "author": row[22] or "",
        "authorUrl": row[23] or "",
        "coverUrl": row[24] or "",
        "seoTitle": row[25] or "",
        "seoDescription": row[26] or "",
        "seoKeywords": _normalize_string_list(row[27]),
        "canonicalUrl": row[28] or "",
        "publishedAt": _iso(row[29]),
        "updatedAt": _iso(row[30]),
        "createdAt": _iso(row[31]),
    }


def load_seed_posts() -> list[dict[str, Any]]:
    if not SEED_PATH.is_file():
        return []
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("slug")]


def seed_payload_to_row(item: dict[str, Any]) -> dict[str, Any]:
    structured = _normalize_structured(item.get("structured"))
    duration_raw = item.get("durationMin", item.get("duration_min", 0))
    try:
        duration_min = max(0, int(duration_raw or 0))
    except (TypeError, ValueError):
        duration_min = 0
    return {
        "slug": str(item.get("slug") or "").strip()[:128],
        "episode": str(item.get("episode") or "").strip()[:32],
        "title": str(item.get("title") or "").strip()[:512],
        "short_title": str(
            item.get("shortTitle") or item.get("short_title") or ""
        ).strip()[:128],
        "rubric_id": str(
            item.get("rubricId") or item.get("rubric_id") or "architecture"
        ).strip()[:64],
        "sort_order": int(item.get("order") or item.get("sort_order") or 0),
        "theory": str(item.get("theory") or ""),
        "lab": str(item.get("lab") or ""),
        "cheatsheet": str(item.get("cheatsheet") or ""),
        "diagram": str(item.get("diagram") or ""),
        "links": _normalize_links(item.get("links")),
        "structured": structured or {},
        "theory_format": _normalize_format(
            item.get("theoryFormat") or item.get("theory_format")
        ),
        "lab_format": _normalize_format(item.get("labFormat") or item.get("lab_format")),
        "cheatsheet_format": _normalize_format(
            item.get("cheatsheetFormat") or item.get("cheatsheet_format")
        ),
        "profiles": _normalize_profiles(item.get("profiles")),
        "level": _normalize_level(item.get("level")),
        "tags": _normalize_string_list(item.get("tags")),
        "excerpt": str(item.get("excerpt") or "").strip()[:2000],
        "duration_min": duration_min,
        "prerequisites": _normalize_prerequisites(item.get("prerequisites")),
        "author": str(item.get("author") or "").strip()[:128],
        "author_url": str(
            item.get("authorUrl") or item.get("author_url") or ""
        ).strip()[:512],
        "cover_url": str(
            item.get("coverUrl") or item.get("cover_url") or ""
        ).strip()[:1024],
        "seo_title": str(
            item.get("seoTitle") or item.get("seo_title") or ""
        ).strip()[:200],
        "seo_description": str(
            item.get("seoDescription") or item.get("seo_description") or ""
        ).strip()[:400],
        "seo_keywords": _normalize_string_list(
            item.get("seoKeywords") or item.get("seo_keywords")
        ),
        "canonical_url": str(
            item.get("canonicalUrl") or item.get("canonical_url") or ""
        ).strip()[:512],
        "published_at": _parse_dt(
            item.get("publishedAt") or item.get("published_at")
        ),
    }


_META_INSERT_COLS = """
    slug, episode, title, short_title, rubric_id, sort_order,
    theory, lab, cheatsheet, diagram, links, structured,
    theory_format, lab_format, cheatsheet_format,
    profiles, level, tags, excerpt, duration_min, prerequisites,
    author, author_url, cover_url, seo_title, seo_description,
    seo_keywords, canonical_url, published_at
"""


def _meta_values(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["slug"],
        row["episode"],
        row["title"],
        row["short_title"],
        row["rubric_id"],
        row["sort_order"],
        row["theory"],
        row["lab"],
        row["cheatsheet"],
        row["diagram"],
        json.dumps(row["links"], ensure_ascii=False),
        json.dumps(row["structured"], ensure_ascii=False),
        row["theory_format"],
        row["lab_format"],
        row["cheatsheet_format"],
        json.dumps(row["profiles"], ensure_ascii=False),
        row["level"],
        json.dumps(row["tags"], ensure_ascii=False),
        row["excerpt"],
        row["duration_min"],
        json.dumps(row["prerequisites"], ensure_ascii=False),
        row["author"],
        row["author_url"],
        row["cover_url"],
        row["seo_title"],
        row["seo_description"],
        json.dumps(row["seo_keywords"], ensure_ascii=False),
        row["canonical_url"],
        row["published_at"],
    )


class LearnService:
    async def count_posts(self) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM learn_posts")
                row = await cur.fetchone()
                return int(row[0] if row else 0)
        finally:
            await release_db_connection(conn)

    async def ensure_seeded(self) -> int:
        """Seed from JSON if table empty. Returns inserted count."""
        if await self.count_posts() > 0:
            return 0
        return await self.reset_to_seed()

    async def reset_to_seed(self) -> int:
        seed = load_seed_posts()
        if not seed:
            raise ValueError("learn_seed.json missing or empty")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM learn_progress")
                await cur.execute("DELETE FROM learn_posts")
                inserted = 0
                for item in seed:
                    row = seed_payload_to_row(item)
                    if not row["slug"] or not row["title"]:
                        continue
                    await cur.execute(
                        f"""
                        INSERT INTO learn_posts ({_META_INSERT_COLS})
                        VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                            %s, %s, %s,
                            %s::jsonb, %s, %s::jsonb, %s, %s, %s::jsonb,
                            %s, %s, %s, %s, %s,
                            %s::jsonb, %s, %s
                        )
                        """,
                        _meta_values(row),
                    )
                    inserted += 1
                return inserted
        finally:
            await release_db_connection(conn)

    async def list_posts(self, *, include_unpublished: bool = False) -> list[dict[str, Any]]:
        await self.ensure_seeded()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if include_unpublished:
                    await cur.execute(
                        f"""
                        SELECT {POST_COLUMNS}
                        FROM learn_posts
                        ORDER BY sort_order ASC, id ASC
                        """
                    )
                else:
                    await cur.execute(
                        f"""
                        SELECT {POST_COLUMNS}
                        FROM learn_posts
                        WHERE published_at <= NOW()
                        ORDER BY sort_order ASC, id ASC
                        """
                    )
                rows = await cur.fetchall()
                return [_row_post(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def get_post(
        self, slug: str, *, include_unpublished: bool = False
    ) -> Optional[dict[str, Any]]:
        await self.ensure_seeded()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if include_unpublished:
                    await cur.execute(
                        f"""
                        SELECT {POST_COLUMNS}
                        FROM learn_posts WHERE slug = %s
                        """,
                        (slug,),
                    )
                else:
                    await cur.execute(
                        f"""
                        SELECT {POST_COLUMNS}
                        FROM learn_posts
                        WHERE slug = %s AND published_at <= NOW()
                        """,
                        (slug,),
                    )
                row = await cur.fetchone()
                return _row_post(row) if row else None
        finally:
            await release_db_connection(conn)

    async def upsert_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = seed_payload_to_row(payload)
        if not row["slug"]:
            raise ValueError("slug is required")
        if not row["title"]:
            raise ValueError("title is required")
        if row["rubric_id"] not in VALID_RUBRICS:
            row["rubric_id"] = "architecture"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    INSERT INTO learn_posts (
                        {_META_INSERT_COLS},
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                        %s, %s, %s,
                        %s::jsonb, %s, %s::jsonb, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, %s,
                        %s::jsonb, %s, %s, NOW()
                    )
                    ON CONFLICT (slug) DO UPDATE SET
                        episode = EXCLUDED.episode,
                        title = EXCLUDED.title,
                        short_title = EXCLUDED.short_title,
                        rubric_id = EXCLUDED.rubric_id,
                        sort_order = EXCLUDED.sort_order,
                        theory = EXCLUDED.theory,
                        lab = EXCLUDED.lab,
                        cheatsheet = EXCLUDED.cheatsheet,
                        diagram = EXCLUDED.diagram,
                        links = EXCLUDED.links,
                        structured = EXCLUDED.structured,
                        theory_format = EXCLUDED.theory_format,
                        lab_format = EXCLUDED.lab_format,
                        cheatsheet_format = EXCLUDED.cheatsheet_format,
                        profiles = EXCLUDED.profiles,
                        level = EXCLUDED.level,
                        tags = EXCLUDED.tags,
                        excerpt = EXCLUDED.excerpt,
                        duration_min = EXCLUDED.duration_min,
                        prerequisites = EXCLUDED.prerequisites,
                        author = EXCLUDED.author,
                        author_url = EXCLUDED.author_url,
                        cover_url = EXCLUDED.cover_url,
                        seo_title = EXCLUDED.seo_title,
                        seo_description = EXCLUDED.seo_description,
                        seo_keywords = EXCLUDED.seo_keywords,
                        canonical_url = EXCLUDED.canonical_url,
                        published_at = EXCLUDED.published_at,
                        updated_at = NOW()
                    RETURNING {POST_COLUMNS}
                    """,
                    _meta_values(row),
                )
                saved = await cur.fetchone()
                return _row_post(saved)
        finally:
            await release_db_connection(conn)

    async def delete_post(self, slug: str) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM learn_posts WHERE slug = %s RETURNING id",
                    (slug,),
                )
                return await cur.fetchone() is not None
        finally:
            await release_db_connection(conn)

    async def schedule_all(self, start_iso: str, interval_days: float) -> list[dict[str, Any]]:
        start = _parse_dt(start_iso)
        step = max(0.0, float(interval_days)) * 24 * 60 * 60
        posts = await self.list_posts(include_unpublished=True)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                for index, post in enumerate(posts):
                    published = start + timedelta(seconds=step * index)
                    await cur.execute(
                        """
                        UPDATE learn_posts
                        SET published_at = %s, updated_at = NOW()
                        WHERE slug = %s
                        """,
                        (published, post["slug"]),
                    )
        finally:
            await release_db_connection(conn)
        return await self.list_posts(include_unpublished=True)

    async def list_progress(self, user_id: int) -> list[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT slug, completed_at
                    FROM learn_progress
                    WHERE user_id = %s
                    ORDER BY completed_at DESC
                    """,
                    (user_id,),
                )
                rows = await cur.fetchall()
                return [
                    {"slug": r[0], "completedAt": _iso(r[1])}
                    for r in rows
                ]
        finally:
            await release_db_connection(conn)

    async def set_progress(
        self, user_id: int, slug: str, *, completed: bool = True
    ) -> dict[str, Any]:
        post = await self.get_post(slug, include_unpublished=True)
        if not post:
            raise ValueError("Post not found")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if completed:
                    await cur.execute(
                        """
                        INSERT INTO learn_progress (user_id, slug, completed_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (user_id, slug) DO UPDATE
                            SET completed_at = NOW()
                        RETURNING slug, completed_at
                        """,
                        (user_id, slug),
                    )
                    row = await cur.fetchone()
                    return {"slug": row[0], "completedAt": _iso(row[1]), "completed": True}
                await cur.execute(
                    """
                    DELETE FROM learn_progress
                    WHERE user_id = %s AND slug = %s
                    """,
                    (user_id, slug),
                )
                return {"slug": slug, "completedAt": None, "completed": False}
        finally:
            await release_db_connection(conn)


learn_service = LearnService()

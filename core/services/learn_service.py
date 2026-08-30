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
    "theory, lab, cheatsheet, diagram, links, "
    "theory_format, lab_format, cheatsheet_format, "
    "published_at, updated_at, created_at"
)

VALID_FORMATS = ("markdown", "html")
VALID_RUBRICS = ("architecture", "api", "data", "frontend", "tools")


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


def _normalize_links(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()[:255]
        href = str(item.get("href") or "").strip()[:1024]
        if label or href:
            out.append({"label": label or href, "href": href or "#"})
    return out


def _row_post(row: tuple) -> dict[str, Any]:
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
        "theoryFormat": _normalize_format(row[12]),
        "labFormat": _normalize_format(row[13]),
        "cheatsheetFormat": _normalize_format(row[14]),
        "publishedAt": _iso(row[15]),
        "updatedAt": _iso(row[16]),
        "createdAt": _iso(row[17]),
    }


def load_seed_posts() -> list[dict[str, Any]]:
    if not SEED_PATH.is_file():
        return []
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("slug")]


def seed_payload_to_row(item: dict[str, Any]) -> dict[str, Any]:
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
        "theory_format": _normalize_format(
            item.get("theoryFormat") or item.get("theory_format")
        ),
        "lab_format": _normalize_format(item.get("labFormat") or item.get("lab_format")),
        "cheatsheet_format": _normalize_format(
            item.get("cheatsheetFormat") or item.get("cheatsheet_format")
        ),
        "published_at": _parse_dt(
            item.get("publishedAt") or item.get("published_at")
        ),
    }


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
                        """
                        INSERT INTO learn_posts (
                            slug, episode, title, short_title, rubric_id, sort_order,
                            theory, lab, cheatsheet, diagram, links,
                            theory_format, lab_format, cheatsheet_format, published_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s::jsonb,
                            %s, %s, %s, %s
                        )
                        """,
                        (
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
                            row["theory_format"],
                            row["lab_format"],
                            row["cheatsheet_format"],
                            row["published_at"],
                        ),
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
                    """
                    INSERT INTO learn_posts (
                        slug, episode, title, short_title, rubric_id, sort_order,
                        theory, lab, cheatsheet, diagram, links,
                        theory_format, lab_format, cheatsheet_format, published_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, NOW()
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
                        theory_format = EXCLUDED.theory_format,
                        lab_format = EXCLUDED.lab_format,
                        cheatsheet_format = EXCLUDED.cheatsheet_format,
                        published_at = EXCLUDED.published_at,
                        updated_at = NOW()
                    RETURNING """
                    + POST_COLUMNS,
                    (
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
                        row["theory_format"],
                        row["lab_format"],
                        row["cheatsheet_format"],
                        row["published_at"],
                    ),
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

"""SMM layer: brands, inbox, publish jobs, automations, analytics."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from database import get_db_connection, release_db_connection

BRAND_PALETTE = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#EC4899",
    "#06B6D4",
    "#84CC16",
]

MAX_OWN_CHANNELS = 20

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _row_brand(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "group_id": r[2],
        "name": r[3],
        "color": r[4],
        "created_at": r[5].isoformat() if r[5] else None,
        "updated_at": r[6].isoformat() if r[6] else None,
    }


def _row_channel(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "brand_id": r[1],
        "network": r[2],
        "external_id": r[3],
        "title": r[4],
        "kind": r[5],
        "role": r[6],
        "color_override": r[7],
        "created_at": r[8].isoformat() if r[8] else None,
    }


def _row_inbox(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "network": r[3],
        "channel_id": r[4],
        "thread_id": r[5],
        "type": r[6],
        "author": r[7],
        "text": r[8],
        "status": r[9],
        "created_at": r[10].isoformat() if r[10] else None,
    }


def _row_job(r: tuple) -> dict[str, Any]:
    media = r[4] if isinstance(r[4], list) else (json.loads(r[4]) if r[4] else [])
    targets = r[5] if isinstance(r[5], list) else (json.loads(r[5]) if r[5] else [])
    adapters = r[6] if isinstance(r[6], dict) else (json.loads(r[6]) if r[6] else {})
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "source_text": r[3],
        "media": media,
        "targets": targets,
        "adapters_result": adapters,
        "publish_at": r[7].isoformat() if r[7] else None,
        "status": r[8],
        "created_at": r[9].isoformat() if r[9] else None,
        "updated_at": r[10].isoformat() if r[10] else None,
    }


def _row_automation(r: tuple) -> dict[str, Any]:
    config = r[4] if isinstance(r[4], dict) else (json.loads(r[4]) if r[4] else {})
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "type": r[3],
        "config": config,
        "enabled": r[5],
        "created_at": r[6].isoformat() if r[6] else None,
        "updated_at": r[7].isoformat() if r[7] else None,
    }


def adapt_for_networks(text: str, media: list[str], targets: list[dict]) -> dict[str, Any]:
    """Network adapters: TG keeps formatting; VK → carousel hint / plain text."""
    networks = {t.get("network") for t in targets}
    result: dict[str, Any] = {}
    if "tg" in networks:
        result["tg"] = {
            "text": text,
            "parse_mode": "HTML",
            "keep_spoiler": True,
            "media": media,
        }
    if "vk" in networks:
        plain = re.sub(r"<[^>]+>", "", text)
        plain = plain.replace("&nbsp;", " ").strip()
        result["vk"] = {
            "text": plain,
            "attachments_mode": "carousel" if len(media) > 1 else ("single" if media else "none"),
            "media": media,
            "poll_hint": False,
        }
    return result


class SmmService:
    async def list_brands(self, user_id: int) -> list[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, group_id, name, color, created_at, updated_at
                    FROM smm_brands WHERE user_id = %s ORDER BY name
                    """,
                    (user_id,),
                )
                rows = await cur.fetchall()
                return [_row_brand(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def create_brand(
        self,
        user_id: int,
        name: str,
        color: str = "#3B82F6",
        group_id: Optional[int] = None,
    ) -> dict:
        if not _HEX_RE.match(color):
            color = BRAND_PALETTE[0]
        if color not in BRAND_PALETTE and not _HEX_RE.match(color):
            color = BRAND_PALETTE[0]
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_brands (user_id, group_id, name, color)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id, group_id, name, color, created_at, updated_at
                    """,
                    (user_id, group_id, name.strip(), color),
                )
                row = await cur.fetchone()
                return _row_brand(row)
        finally:
            await release_db_connection(conn)

    async def get_brand(self, user_id: int, brand_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, group_id, name, color, created_at, updated_at
                    FROM smm_brands WHERE id = %s AND user_id = %s
                    """,
                    (brand_id, user_id),
                )
                row = await cur.fetchone()
                return _row_brand(row) if row else None
        finally:
            await release_db_connection(conn)

    async def update_brand(
        self,
        user_id: int,
        brand_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None,
        group_id: Optional[int] = None,
    ) -> Optional[dict]:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return None
        new_name = name.strip() if name else brand["name"]
        new_color = color if color and _HEX_RE.match(color) else brand["color"]
        new_group = group_id if group_id is not None else brand["group_id"]
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_brands
                    SET name = %s, color = %s, group_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, group_id, name, color, created_at, updated_at
                    """,
                    (new_name, new_color, new_group, brand_id, user_id),
                )
                row = await cur.fetchone()
                return _row_brand(row) if row else None
        finally:
            await release_db_connection(conn)

    async def delete_brand(self, user_id: int, brand_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_brands WHERE id = %s AND user_id = %s",
                    (brand_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def list_channels(self, user_id: int, brand_id: int) -> list[dict]:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, network, external_id, title, kind, role,
                           color_override, created_at
                    FROM smm_brand_channels WHERE brand_id = %s ORDER BY role, title
                    """,
                    (brand_id,),
                )
                rows = await cur.fetchall()
                return [_row_channel(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def count_own_channels(self, user_id: int) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*) FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE b.user_id = %s AND c.role = 'own'
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                return int(row[0]) if row else 0
        finally:
            await release_db_connection(conn)

    async def add_channel(
        self,
        user_id: int,
        brand_id: int,
        network: str,
        external_id: str,
        title: Optional[str] = None,
        kind: str = "channel",
        role: str = "own",
        color_override: Optional[str] = None,
    ) -> dict:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        if network not in ("tg", "vk"):
            raise ValueError("network must be tg or vk")
        if role not in ("own", "competitor", "source"):
            raise ValueError("invalid role")
        if kind not in ("channel", "group", "public"):
            raise ValueError("invalid kind")
        if role == "own":
            count = await self.count_own_channels(user_id)
            if count >= MAX_OWN_CHANNELS:
                raise ValueError(f"Own channel limit ({MAX_OWN_CHANNELS}) reached")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_brand_channels
                        (brand_id, network, external_id, title, kind, role, color_override)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, brand_id, network, external_id, title, kind, role,
                              color_override, created_at
                    """,
                    (
                        brand_id,
                        network,
                        str(external_id).strip(),
                        title,
                        kind,
                        role,
                        color_override,
                    ),
                )
                row = await cur.fetchone()
                return _row_channel(row)
        finally:
            await release_db_connection(conn)

    async def update_channel(
        self,
        user_id: int,
        brand_id: int,
        channel_id: int,
        **fields: Any,
    ) -> Optional[dict]:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return None
        allowed = {"title", "kind", "role", "color_override", "external_id"}
        updates = []
        params: list[Any] = []
        for key, val in fields.items():
            if key in allowed and val is not None:
                updates.append(f"{key} = %s")
                params.append(val)
        if not updates:
            channels = await self.list_channels(user_id, brand_id)
            return next((c for c in channels if c["id"] == channel_id), None)
        params.extend([channel_id, brand_id])
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_brand_channels SET {', '.join(updates)}
                    WHERE id = %s AND brand_id = %s
                    RETURNING id, brand_id, network, external_id, title, kind, role,
                              color_override, created_at
                    """,
                    params,
                )
                row = await cur.fetchone()
                return _row_channel(row) if row else None
        finally:
            await release_db_connection(conn)

    async def delete_channel(self, user_id: int, brand_id: int, channel_id: int) -> bool:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return False
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_brand_channels WHERE id = %s AND brand_id = %s",
                    (channel_id, brand_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def list_inbox(
        self,
        user_id: int,
        brand_id: Optional[int] = None,
        network: Optional[str] = None,
        type_: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[int] = None,
    ) -> dict:
        conditions = ["user_id = %s"]
        params: list[Any] = [user_id]
        if brand_id is not None:
            conditions.append("brand_id = %s")
            params.append(brand_id)
        if network:
            conditions.append("network = %s")
            params.append(network)
        if type_:
            conditions.append("type = %s")
            params.append(type_)
        if status:
            conditions.append("status = %s")
            params.append(status)
        if cursor is not None:
            conditions.append("id < %s")
            params.append(cursor)
        params.append(min(limit, 100))
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT id, user_id, brand_id, network, channel_id, thread_id,
                           type, author, text, status, created_at
                    FROM smm_inbox_items
                    WHERE {where}
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    params,
                )
                rows = await cur.fetchall()
                items = [_row_inbox(r) for r in rows]
                next_cursor = items[-1]["id"] if items else None
                return {"items": items, "next_cursor": next_cursor}
        finally:
            await release_db_connection(conn)

    async def create_inbox_item(self, user_id: int, data: dict) -> dict:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_inbox_items
                        (user_id, brand_id, network, channel_id, thread_id, type, author, text, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, brand_id, network, channel_id, thread_id,
                              type, author, text, status, created_at
                    """,
                    (
                        user_id,
                        data.get("brand_id"),
                        data["network"],
                        data.get("channel_id"),
                        data.get("thread_id"),
                        data["type"],
                        data.get("author"),
                        data.get("text"),
                        data.get("status", "new"),
                    ),
                )
                row = await cur.fetchone()
                return _row_inbox(row)
        finally:
            await release_db_connection(conn)

    async def update_inbox_status(
        self, user_id: int, item_id: int, status: str
    ) -> Optional[dict]:
        if status not in ("new", "read", "replied", "archived"):
            raise ValueError("invalid status")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_inbox_items SET status = %s
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, brand_id, network, channel_id, thread_id,
                              type, author, text, status, created_at
                    """,
                    (status, item_id, user_id),
                )
                row = await cur.fetchone()
                return _row_inbox(row) if row else None
        finally:
            await release_db_connection(conn)

    async def reply_inbox(self, user_id: int, item_id: int, text: str) -> Optional[dict]:
        item = await self.update_inbox_status(user_id, item_id, "replied")
        if not item:
            return None
        item["reply_text"] = text
        item["reply_queued"] = True
        return item

    async def create_job(
        self,
        user_id: int,
        brand_id: Optional[int],
        text: str,
        media: Optional[list[str]] = None,
        targets: Optional[list[dict]] = None,
        publish_at: Optional[str] = None,
        adapt: bool = True,
        status: str = "ready",
    ) -> dict:
        media = media or []
        targets = targets or []
        adapters = adapt_for_networks(text, media, targets) if adapt else {}
        pub_at = None
        if publish_at:
            try:
                pub_at = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
            except ValueError:
                pub_at = None
        if pub_at and status == "ready":
            status = "scheduled"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_publish_jobs
                        (user_id, brand_id, source_text, media, targets, adapters_result, publish_at, status)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                    RETURNING id, user_id, brand_id, source_text, media, targets, adapters_result,
                              publish_at, status, created_at, updated_at
                    """,
                    (
                        user_id,
                        brand_id,
                        text,
                        json.dumps(media),
                        json.dumps(targets),
                        json.dumps(adapters),
                        pub_at,
                        status,
                    ),
                )
                row = await cur.fetchone()
                return _row_job(row)
        finally:
            await release_db_connection(conn)

    async def list_jobs(
        self,
        user_id: int,
        brand_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict]:
        conditions = ["user_id = %s"]
        params: list[Any] = [user_id]
        if brand_id is not None:
            conditions.append("brand_id = %s")
            params.append(brand_id)
        if date_from:
            conditions.append("COALESCE(publish_at, created_at) >= %s::timestamptz")
            params.append(date_from)
        if date_to:
            conditions.append("COALESCE(publish_at, created_at) <= %s::timestamptz")
            params.append(date_to)
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT id, user_id, brand_id, source_text, media, targets, adapters_result,
                           publish_at, status, created_at, updated_at
                    FROM smm_publish_jobs
                    WHERE {where}
                    ORDER BY COALESCE(publish_at, created_at) DESC
                    LIMIT 500
                    """,
                    params,
                )
                rows = await cur.fetchall()
                return [_row_job(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def update_job(self, user_id: int, job_id: int, **fields: Any) -> Optional[dict]:
        allowed = {"source_text", "media", "targets", "publish_at", "status", "adapters_result"}
        updates = []
        params: list[Any] = []
        for key, val in fields.items():
            if key not in allowed or val is None:
                continue
            if key in ("media", "targets", "adapters_result"):
                updates.append(f"{key} = %s::jsonb")
                params.append(json.dumps(val))
            elif key == "publish_at":
                updates.append("publish_at = %s")
                if isinstance(val, str):
                    try:
                        params.append(datetime.fromisoformat(val.replace("Z", "+00:00")))
                    except ValueError:
                        params.append(None)
                else:
                    params.append(val)
            else:
                updates.append(f"{key} = %s")
                params.append(val)
        if not updates:
            return None
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([job_id, user_id])
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_publish_jobs SET {', '.join(updates)}
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, brand_id, source_text, media, targets, adapters_result,
                              publish_at, status, created_at, updated_at
                    """,
                    params,
                )
                row = await cur.fetchone()
                return _row_job(row) if row else None
        finally:
            await release_db_connection(conn)

    async def import_csv(self, user_id: int, brand_id: Optional[int], content: str) -> dict:
        reader = csv.DictReader(io.StringIO(content))
        created = []
        errors = []
        for i, row in enumerate(reader, start=2):
            text = (row.get("text") or row.get("post_text") or row.get("content") or "").strip()
            if not text:
                errors.append({"line": i, "error": "empty text"})
                continue
            publish_at = (row.get("publish_at") or row.get("scheduled_at") or "").strip() or None
            network = (row.get("network") or "").strip().lower()
            external_id = (row.get("channel") or row.get("external_id") or "").strip()
            targets = []
            if network in ("tg", "vk") and external_id:
                targets = [{"network": network, "external_id": external_id}]
            try:
                job = await self.create_job(
                    user_id=user_id,
                    brand_id=brand_id,
                    text=text,
                    media=[],
                    targets=targets,
                    publish_at=publish_at,
                    adapt=True,
                    status="draft",
                )
                created.append(job["id"])
            except Exception as exc:
                errors.append({"line": i, "error": str(exc)})
        return {"created": len(created), "job_ids": created, "errors": errors}

    async def list_automations(self, user_id: int, brand_id: Optional[int] = None) -> list[dict]:
        conditions = ["user_id = %s"]
        params: list[Any] = [user_id]
        if brand_id is not None:
            conditions.append("brand_id = %s")
            params.append(brand_id)
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT id, user_id, brand_id, type, config, enabled, created_at, updated_at
                    FROM smm_automations WHERE {where} ORDER BY id DESC
                    """,
                    params,
                )
                rows = await cur.fetchall()
                return [_row_automation(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def create_automation(
        self,
        user_id: int,
        brand_id: int,
        type_: str,
        config: dict,
        enabled: bool = True,
    ) -> dict:
        if type_ not in ("rss", "tg_repost", "mention"):
            raise ValueError("type must be rss, tg_repost, or mention")
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_automations (user_id, brand_id, type, config, enabled)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    RETURNING id, user_id, brand_id, type, config, enabled, created_at, updated_at
                    """,
                    (user_id, brand_id, type_, json.dumps(config), enabled),
                )
                row = await cur.fetchone()
                return _row_automation(row)
        finally:
            await release_db_connection(conn)

    async def update_automation(
        self, user_id: int, automation_id: int, **fields: Any
    ) -> Optional[dict]:
        updates = []
        params: list[Any] = []
        if "config" in fields and fields["config"] is not None:
            updates.append("config = %s::jsonb")
            params.append(json.dumps(fields["config"]))
        if "enabled" in fields and fields["enabled"] is not None:
            updates.append("enabled = %s")
            params.append(fields["enabled"])
        if "type" in fields and fields["type"] is not None:
            updates.append("type = %s")
            params.append(fields["type"])
        if "brand_id" in fields and fields["brand_id"] is not None:
            updates.append("brand_id = %s")
            params.append(fields["brand_id"])
        if not updates:
            return None
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([automation_id, user_id])
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_automations SET {', '.join(updates)}
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, brand_id, type, config, enabled, created_at, updated_at
                    """,
                    params,
                )
                row = await cur.fetchone()
                return _row_automation(row) if row else None
        finally:
            await release_db_connection(conn)

    async def delete_automation(self, user_id: int, automation_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_automations WHERE id = %s AND user_id = %s",
                    (automation_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def analytics_overview(self, user_id: int, brand_id: Optional[int], period: str = "7d") -> dict:
        days = 7 if period == "7d" else (30 if period == "30d" else 7)
        since = datetime.utcnow() - timedelta(days=days)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COALESCE(SUM(views),0), COALESCE(SUM(likes),0),
                           COALESCE(SUM(comments),0), COALESCE(SUM(reposts),0), COUNT(*)
                    FROM tg_posts
                    WHERE user_id = %s AND created_at >= %s AND status != 'deleted'
                    """,
                    (user_id, since),
                )
                tg = await cur.fetchone()
                await cur.execute(
                    """
                    SELECT COALESCE(SUM(views),0), COALESCE(SUM(likes),0),
                           COALESCE(SUM(comments),0), COALESCE(SUM(reposts),0), COUNT(*)
                    FROM vk_posts
                    WHERE user_id = %s AND created_at >= %s AND status != 'deleted'
                    """,
                    (user_id, since),
                )
                vk = await cur.fetchone()
            tg_views, tg_likes, tg_comments, tg_reposts, tg_count = tg
            vk_views, vk_likes, vk_comments, vk_reposts, vk_count = vk
            total_views = int(tg_views) + int(vk_views)
            total_eng = (
                int(tg_likes) + int(tg_comments) + int(tg_reposts)
                + int(vk_likes) + int(vk_comments) + int(vk_reposts)
            )
            total_posts = int(tg_count) + int(vk_count)
            er = round((total_eng / total_views) * 100, 2) if total_views else 0.0
            return {
                "period": period,
                "brand_id": brand_id,
                "reach": total_views,
                "engagement": total_eng,
                "er": er,
                "posts": total_posts,
                "subscriber_growth": 0,
                "by_network": {
                    "tg": {
                        "views": int(tg_views),
                        "likes": int(tg_likes),
                        "comments": int(tg_comments),
                        "reposts": int(tg_reposts),
                        "posts": int(tg_count),
                    },
                    "vk": {
                        "views": int(vk_views),
                        "likes": int(vk_likes),
                        "comments": int(vk_comments),
                        "reposts": int(vk_reposts),
                        "posts": int(vk_count),
                    },
                },
            }
        finally:
            await release_db_connection(conn)

    async def analytics_posts(
        self, user_id: int, brand_id: Optional[int], sort: str = "er", limit: int = 20
    ) -> list[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, post_text, views, likes, comments, reposts, 'tg' AS network, created_at
                    FROM tg_posts WHERE user_id = %s AND status != 'deleted'
                    UNION ALL
                    SELECT id, post_text, views, likes, comments, reposts, 'vk' AS network, created_at
                    FROM vk_posts WHERE user_id = %s AND status != 'deleted'
                    """,
                    (user_id, user_id),
                )
                rows = await cur.fetchall()
            items = []
            for r in rows:
                views = int(r[2] or 0)
                eng = int(r[3] or 0) + int(r[4] or 0) + int(r[5] or 0)
                er = (eng / views * 100) if views else 0.0
                items.append(
                    {
                        "id": r[0],
                        "text": (r[1] or "")[:200],
                        "views": views,
                        "likes": int(r[3] or 0),
                        "comments": int(r[4] or 0),
                        "reposts": int(r[5] or 0),
                        "er": round(er, 2),
                        "network": r[6],
                        "created_at": r[7].isoformat() if r[7] else None,
                        "brand_id": brand_id,
                    }
                )
            key = "er" if sort == "er" else "views"
            items.sort(key=lambda x: x[key], reverse=True)
            return items[:limit]
        finally:
            await release_db_connection(conn)

    async def analytics_growth(self, user_id: int, brand_id: Optional[int]) -> dict:
        return {
            "brand_id": brand_id,
            "points": [],
            "message": "Subscriber growth tracking will populate as collectors ingest metrics",
        }

    async def best_times(
        self,
        user_id: int,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        horizon_days: int = 30,
    ) -> dict:
        since = datetime.utcnow() - timedelta(days=horizon_days)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT EXTRACT(DOW FROM COALESCE(publish_at, created_at)) AS dow,
                           EXTRACT(HOUR FROM COALESCE(publish_at, created_at)) AS hour,
                           AVG(views + likes * 3 + comments * 5 + reposts * 4) AS score
                    FROM tg_posts
                    WHERE user_id = %s AND COALESCE(publish_at, created_at) >= %s
                    GROUP BY dow, hour
                    ORDER BY score DESC NULLS LAST
                    LIMIT 24
                    """,
                    (user_id, since),
                )
                rows = await cur.fetchall()
            slots = [
                {
                    "weekday": int(r[0] or 0),
                    "hour": int(r[1] or 0),
                    "score": round(float(r[2] or 0), 2),
                }
                for r in rows
            ]
            if not slots:
                # Default heuristic peaks
                slots = [
                    {"weekday": 2, "hour": 10, "score": 50.0},
                    {"weekday": 3, "hour": 12, "score": 48.0},
                    {"weekday": 4, "hour": 18, "score": 55.0},
                    {"weekday": 1, "hour": 9, "score": 40.0},
                ]
            return {
                "brand_id": brand_id,
                "channel_id": channel_id,
                "horizon_days": horizon_days,
                "slots": slots,
            }
        finally:
            await release_db_connection(conn)

    async def competitor_posts(self, user_id: int, channel_id: int) -> list[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE c.id = %s AND b.user_id = %s AND c.role = 'competitor'
                    """,
                    (channel_id, user_id),
                )
                ch = await cur.fetchone()
                if not ch:
                    return []
                await cur.execute(
                    """
                    SELECT id, external_post_id, post_text, views, likes, comments, reposts,
                           posted_at, collected_at
                    FROM smm_competitor_snapshots
                    WHERE channel_id = %s
                    ORDER BY COALESCE(posted_at, collected_at) DESC
                    LIMIT 50
                    """,
                    (channel_id,),
                )
                rows = await cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "external_post_id": r[1],
                        "text": r[2],
                        "views": r[3],
                        "likes": r[4],
                        "comments": r[5],
                        "reposts": r[6],
                        "posted_at": r[7].isoformat() if r[7] else None,
                        "collected_at": r[8].isoformat() if r[8] else None,
                    }
                    for r in rows
                ]
        finally:
            await release_db_connection(conn)

    async def add_competitor_snapshot(
        self, channel_id: int, data: dict
    ) -> dict:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_competitor_snapshots
                        (channel_id, external_post_id, post_text, views, likes, comments, reposts, posted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        channel_id,
                        data.get("external_post_id"),
                        data.get("post_text"),
                        data.get("views", 0),
                        data.get("likes", 0),
                        data.get("comments", 0),
                        data.get("reposts", 0),
                        data.get("posted_at"),
                    ),
                )
                row = await cur.fetchone()
                return {"id": row[0]}
        finally:
            await release_db_connection(conn)


smm_service = SmmService()

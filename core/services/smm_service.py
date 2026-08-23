"""SMM layer: brands, inbox, publish jobs, automations, analytics."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from database import get_db_connection, release_db_connection
from exceptions import QuotaExceededError
from services.quota_service import (
    ensure_monthly_post_quota,
    ensure_smm_feature,
    ensure_smm_limit,
    get_user_tariff,
    plan_feature,
    plan_limit,
)

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


def _parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def _iso_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _channel_id_equal(left: str, right: str) -> bool:
    a = left.strip()
    b = right.strip()
    if not a or not b:
        return False
    if a == b:
        return True
    if a.lstrip("-") == b.lstrip("-"):
        return True
    try:
        return int(a) == int(b)
    except (TypeError, ValueError):
        return False


def _iter_channel_tokens(value: Any) -> list[str]:
    tokens: list[str] = []
    parsed = _parse_json_field(value, value)
    if parsed is None:
        return tokens
    if isinstance(parsed, list):
        for item in parsed:
            tokens.extend(_iter_channel_tokens(item))
        return tokens
    if isinstance(parsed, dict):
        for key in ("external_id", "id", "chat_id"):
            raw = parsed.get(key)
            if raw is not None and raw != "":
                tokens.append(str(raw).strip())
        return tokens
    text = str(parsed).strip()
    if text:
        tokens.append(text)
    return tokens


def _match_channel(channels: list[dict], network: str, *candidates: Any) -> Optional[dict]:
    tokens: list[str] = []
    for cand in candidates:
        tokens.extend(_iter_channel_tokens(cand))
    if not tokens:
        return None
    for ch in channels:
        if ch.get("network") != network:
            continue
        ext = str(ch.get("external_id") or "").strip()
        if not ext:
            continue
        if any(_channel_id_equal(ext, token) for token in tokens):
            return ch
    return None


def _external_id_variants(external_id: Any) -> list[str]:
    ext = str(external_id or "").strip()
    if not ext:
        return []
    variants = [ext]
    stripped = ext.lstrip("-")
    if stripped and stripped != ext:
        variants.append(stripped)
    try:
        n = int(ext)
        variants.extend([str(n), str(abs(n)), str(-abs(n))])
    except (TypeError, ValueError):
        pass
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _posts_channel_where(network: str, external_id: Any, table_alias: str = "") -> tuple[str, list[Any]]:
    prefix = f"{table_alias}." if table_alias else ""
    variants = _external_id_variants(external_id)
    if not variants:
        return "FALSE", []
    parts: list[str] = []
    params: list[Any] = []
    target_col = "target_channels" if network == "tg" else "target_groups"
    chat_col = "telegram_chat_id" if network == "tg" else None
    for v in variants:
        parts.append(f"{prefix}domain = %s")
        params.append(v)
        if chat_col:
            parts.append(f"{prefix}{chat_col} = %s")
            params.append(v)
        parts.append(f"{prefix}{target_col} ? %s")
        params.append(v)
        parts.append(f"{prefix}{target_col} @> %s::jsonb")
        params.append(json.dumps([v]))
    return "(" + " OR ".join(parts) + ")", params


def _row_channel(r: tuple) -> dict[str, Any]:
    # Supports ops, comments, and channel-flow config columns
    out = {
        "id": r[0],
        "brand_id": r[1],
        "network": r[2],
        "external_id": r[3],
        "title": r[4],
        "kind": r[5],
        "role": r[6],
        "color_override": r[7],
        "created_at": r[8].isoformat() if r[8] else None,
        "publish_enabled": True,
        "collect_enabled": False,
        "discussion_external_id": None,
        "discussion_title": None,
        "comments_collect_enabled": False,
        "alert_enabled": False,
        "save_conditions": [],
        "conditions_mode": "any_of",
        "processing": {},
        "publish_targets": [],
        "alert_delivery": {},
        "alert_rules": [],
    }
    if len(r) > 9:
        out["publish_enabled"] = bool(r[9]) if r[9] is not None else True
    if len(r) > 10:
        out["collect_enabled"] = bool(r[10]) if r[10] is not None else False
    if len(r) > 11:
        out["discussion_external_id"] = r[11]
    if len(r) > 12:
        out["discussion_title"] = r[12]
    if len(r) > 13:
        out["comments_collect_enabled"] = bool(r[13]) if r[13] is not None else False
    if len(r) > 14:
        out["alert_enabled"] = bool(r[14]) if r[14] is not None else False
    if len(r) > 15:
        sc = _parse_json_field(r[15], [])
        out["save_conditions"] = sc if isinstance(sc, list) else []
    if len(r) > 16:
        proc = _parse_json_field(r[16], {})
        out["processing"] = proc if isinstance(proc, dict) else {}
    if len(r) > 17:
        delivery = _parse_json_field(r[17], {})
        out["alert_delivery"] = delivery if isinstance(delivery, dict) else {}
    if len(r) > 18:
        rules = _parse_json_field(r[18], [])
        out["alert_rules"] = rules if isinstance(rules, list) else []
    if len(r) > 19:
        mode = r[19] or "any_of"
        out["conditions_mode"] = mode if mode in ("any_of", "all_of") else "any_of"
    if len(r) > 20:
        targets = _parse_json_field(r[20], [])
        parsed: list[int] = []
        if isinstance(targets, list):
            for x in targets:
                try:
                    parsed.append(int(x))
                except (TypeError, ValueError):
                    continue
        out["publish_targets"] = parsed
    if len(r) > 21:
        out["auth_status"] = r[21] or "unknown"
    if len(r) > 22:
        out["auth_checked_at"] = r[22].isoformat() if r[22] else None
    if len(r) > 23:
        out["auth_error"] = r[23]
    if len(r) > 24:
        caps = _parse_json_field(r[24], {})
        out["auth_capabilities"] = caps if isinstance(caps, dict) else {}
    return out


def _row_inbox(r: tuple) -> dict[str, Any]:
    out = {
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
        "external_msg_id": None,
        "edited_text": None,
        "meta": {},
    }
    if len(r) > 11:
        out["external_msg_id"] = r[11]
    if len(r) > 12:
        out["edited_text"] = r[12]
    if len(r) > 13:
        meta = r[13]
        out["meta"] = meta if isinstance(meta, dict) else (json.loads(meta) if meta else {})
    return out


CHANNEL_SELECT = """
id, brand_id, network, external_id, title, kind, role,
color_override, created_at, publish_enabled, collect_enabled,
discussion_external_id, discussion_title, comments_collect_enabled,
alert_enabled, save_conditions, processing, alert_delivery, alert_rules,
conditions_mode, publish_targets,
auth_status, auth_checked_at, auth_error, auth_capabilities
"""

CHANNEL_RETURNING = CHANNEL_SELECT
CHANNEL_FIELD_COUNT = 25

INBOX_SELECT = """
id, user_id, brand_id, network, channel_id, thread_id,
type, author, text, status, created_at, external_msg_id, edited_text, meta
"""


def _row_job(r: tuple) -> dict[str, Any]:
    media = r[4] if isinstance(r[4], list) else (json.loads(r[4]) if r[4] else [])
    targets = r[5] if isinstance(r[5], list) else (json.loads(r[5]) if r[5] else [])
    adapters = r[6] if isinstance(r[6], dict) else (json.loads(r[6]) if r[6] else {})
    out = {
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
        "retry_count": 0,
        "last_error": None,
    }
    if len(r) > 11:
        out["retry_count"] = int(r[11] or 0)
    if len(r) > 12:
        out["last_error"] = r[12]
    return out


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
        brands = await self.list_brands(user_id)
        await ensure_smm_limit(user_id, "max_brands", len(brands), units=1)
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
                    f"""
                    SELECT {CHANNEL_SELECT}
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
            await ensure_smm_limit(user_id, "max_own_channels", count, units=1)
        if role == "competitor":
            await ensure_smm_feature(user_id, "competitors")

        ext = str(external_id or "").strip()
        if not ext:
            raise ValueError("Укажите ID канала")

        # Friendly duplicate check before INSERT (UNIQUE brand_id, network, external_id)
        existing = await self.list_channels(user_id, brand_id)
        for ch in existing:
            if ch.get("network") != network:
                continue
            other = str(ch.get("external_id") or "").strip()
            same = other == ext or other.lstrip("-") == ext.lstrip("-")
            if not same:
                try:
                    same = int(other) == int(ext)
                except (TypeError, ValueError):
                    same = False
            if same:
                raise ValueError(
                    f"Канал уже добавлен: «{ch.get('title') or other}» "
                    f"({network}/{other}, роль {ch.get('role')}). "
                    f"Откройте его в списке или удалите перед повторным добавлением."
                )

        from services.platform_auth_service import platform_auth_service

        # Soft probe: channels can always be created; ownership required only for publish.
        auth_probe: dict[str, Any] = {
            "auth_status": "unknown",
            "auth_error": None,
            "auth_capabilities": {},
            "auth_checked_at": datetime.utcnow(),
        }
        if role == "competitor":
            auth_probe["auth_status"] = "not_required"
        else:
            auth_probe = await platform_auth_service.probe_channel_access(
                user_id, network, ext, role, strict=False
            )

        is_owned = auth_probe.get("auth_status") == "connected"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        f"""
                        INSERT INTO smm_brand_channels
                            (brand_id, network, external_id, title, kind, role, color_override,
                             publish_enabled, collect_enabled,
                             auth_status, auth_error, auth_checked_at, auth_capabilities)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        RETURNING {CHANNEL_RETURNING}
                        """,
                        (
                            brand_id,
                            network,
                            ext,
                            title,
                            kind,
                            role,
                            color_override,
                            role == "own" and is_owned,
                            role in ("source", "own"),
                            auth_probe.get("auth_status", "unknown"),
                            auth_probe.get("auth_error"),
                            auth_probe.get("auth_checked_at") or datetime.utcnow(),
                            json.dumps(
                                auth_probe.get("auth_capabilities") or {}, ensure_ascii=False
                            ),
                        ),
                    )
                except Exception as exc:
                    msg = str(exc).lower()
                    if "unique" in msg or "duplicate" in msg:
                        raise ValueError(
                            f"Канал {network}/{ext} уже есть у этого бренда"
                        ) from exc
                    raise
                row = await cur.fetchone()
                return _row_channel(row)
        finally:
            await release_db_connection(conn)

    async def get_channel(self, user_id: int, channel_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT c.id, c.brand_id, c.network, c.external_id, c.title, c.kind, c.role,
                           c.color_override, c.created_at, c.publish_enabled, c.collect_enabled,
                           c.discussion_external_id, c.discussion_title, c.comments_collect_enabled,
                           c.alert_enabled, c.save_conditions, c.processing, c.alert_delivery, c.alert_rules,
                           c.conditions_mode, c.publish_targets,
                           c.auth_status, c.auth_checked_at, c.auth_error, c.auth_capabilities,
                           b.name AS brand_name, b.color AS brand_color
                    FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE c.id = %s AND b.user_id = %s
                    """,
                    (channel_id, user_id),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                ch = _row_channel(row[:CHANNEL_FIELD_COUNT])
                ch["brand_name"] = row[CHANNEL_FIELD_COUNT]
                ch["brand_color"] = row[CHANNEL_FIELD_COUNT + 1]
                return ch
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
        existing = await self.get_channel(user_id, channel_id)
        if not existing:
            return None

        from services.platform_auth_service import platform_auth_service

        await platform_auth_service.validate_channel_update(user_id, existing, fields)

        allowed = {
            "title",
            "kind",
            "role",
            "color_override",
            "external_id",
            "publish_enabled",
            "collect_enabled",
            "discussion_external_id",
            "discussion_title",
            "comments_collect_enabled",
            "alert_enabled",
            "save_conditions",
            "conditions_mode",
            "processing",
            "publish_targets",
            "alert_delivery",
            "alert_rules",
        }
        json_fields = {
            "save_conditions",
            "processing",
            "publish_targets",
            "alert_delivery",
            "alert_rules",
        }
        updates = []
        params: list[Any] = []
        for key, val in fields.items():
            if key not in allowed:
                continue
            # allow clearing discussion ids with empty string → NULL
            if key in ("discussion_external_id", "discussion_title") and val == "":
                val = None
            if key == "conditions_mode" and val is not None:
                val = val if val in ("any_of", "all_of") else "any_of"
            if key == "publish_targets" and val is not None:
                if not isinstance(val, list):
                    val = []
                val = [int(x) for x in val if isinstance(x, (int, float)) or str(x).isdigit()]
            if key in json_fields and val is not None:
                val = json.dumps(val, ensure_ascii=False)
            if val is not None or key in ("discussion_external_id", "discussion_title"):
                updates.append(f"{key} = %s")
                params.append(val)
        if "external_id" in fields or "role" in fields:
            updates.append("auth_status = %s")
            params.append("unknown")
            updates.append("auth_checked_at = NULL")
            updates.append("auth_error = NULL")
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
                    RETURNING {CHANNEL_RETURNING}
                    """,
                    params,
                )
                row = await cur.fetchone()
                ch = _row_channel(row) if row else None
                if ch and ("external_id" in fields or "role" in fields):
                    from services.platform_auth_service import platform_auth_service

                    probe = await platform_auth_service.probe_channel_access(
                        user_id,
                        ch["network"],
                        ch["external_id"],
                        ch.get("role") or "own",
                        strict=False,
                    )
                    await platform_auth_service.persist_channel_auth(channel_id, probe)
                    # Ownership lost → force publish off
                    if (
                        ch.get("role") == "own"
                        and probe.get("auth_status") != "connected"
                        and ch.get("publish_enabled")
                    ):
                        await cur.execute(
                            """
                            UPDATE smm_brand_channels
                            SET publish_enabled = FALSE
                            WHERE id = %s
                            """,
                            (channel_id,),
                        )
                    refreshed = await self.get_channel(user_id, channel_id)
                    return refreshed or ch
                return ch
        finally:
            await release_db_connection(conn)

    async def list_all_channels(
        self, user_id: int, brand_id: Optional[int] = None
    ) -> list[dict]:
        conditions = ["b.user_id = %s"]
        params: list[Any] = [user_id]
        if brand_id is not None:
            conditions.append("c.brand_id = %s")
            params.append(brand_id)
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT c.id, c.brand_id, c.network, c.external_id, c.title, c.kind, c.role,
                           c.color_override, c.created_at, c.publish_enabled, c.collect_enabled,
                           c.discussion_external_id, c.discussion_title, c.comments_collect_enabled,
                           c.alert_enabled, c.save_conditions, c.processing, c.alert_delivery, c.alert_rules,
                           c.conditions_mode, c.publish_targets,
                           c.auth_status, c.auth_checked_at, c.auth_error, c.auth_capabilities,
                           b.name AS brand_name, b.color AS brand_color
                    FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE {where}
                    ORDER BY b.name, c.role, c.title
                    """,
                    params,
                )
                rows = await cur.fetchall()
                result = []
                for r in rows:
                    ch = _row_channel(r[:CHANNEL_FIELD_COUNT])
                    ch["brand_name"] = r[CHANNEL_FIELD_COUNT]
                    ch["brand_color"] = r[CHANNEL_FIELD_COUNT + 1]
                    result.append(ch)
                return result
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
                           type, author, text, status, created_at, external_msg_id, edited_text, meta
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
        if status not in ("new", "read", "replied", "archived", "reply_failed", "in_progress"):
            raise ValueError("invalid status")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_inbox_items SET status = %s
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, brand_id, network, channel_id, thread_id,
                              type, author, text, status, created_at, external_msg_id, edited_text, meta
                    """,
                    (status, item_id, user_id),
                )
                row = await cur.fetchone()
                return _row_inbox(row) if row else None
        finally:
            await release_db_connection(conn)

    async def reply_inbox(self, user_id: int, item_id: int, text: str) -> Optional[dict]:
        await ensure_smm_feature(user_id, "inbox_reply")
        item = await self.get_inbox_item(user_id, item_id)
        if not item:
            return None

        # Fast path: TG comment → direct Telethon reply_to (bypass publish jobs)
        if item.get("type") == "comment" and item.get("network") == "tg":
            return await self._reply_tg_comment(user_id, item, text)

        targets = []
        if item.get("channel_id"):
            channels = await self.list_all_channels(user_id)
            ch = next((c for c in channels if c["id"] == item["channel_id"]), None)
            if ch:
                targets = [{"network": ch["network"], "external_id": ch["external_id"]}]
        if not targets and item.get("network"):
            thread = item.get("thread_id")
            if not thread:
                raise ValueError("Cannot resolve reply target")
            targets = [{"network": item["network"], "external_id": thread}]
        job = await self.create_job(
            user_id=user_id,
            brand_id=item.get("brand_id"),
            text=text,
            media=[],
            targets=targets,
            adapt=True,
            status="ready",
        )
        executed = await self.execute_job(job)
        final = executed.get("status") if executed else "failed"
        if final in ("published", "partial"):
            updated = await self.update_inbox_status(user_id, item_id, "replied")
        else:
            updated = await self.update_inbox_status(user_id, item_id, "reply_failed")
        if updated:
            updated["reply_text"] = text
            updated["reply_job_id"] = job["id"]
            updated["reply_queued"] = False
            updated["reply_status"] = final
        return updated

    async def _reply_tg_comment(self, user_id: int, item: dict, text: str) -> dict:
        """Direct reply in discussion chat via tg-bot."""
        import httpx
        from config import settings

        await ensure_monthly_post_quota(user_id, units=1)
        meta = item.get("meta") or {}
        chat_id = item.get("thread_id") or meta.get("discussion_id")
        reply_to = meta.get("tg_msg_id")
        if not reply_to and item.get("external_msg_id"):
            # external_msg_id like tg:{chat}:{msg_id}
            parts = str(item["external_msg_id"]).split(":")
            if len(parts) >= 3 and parts[-1].isdigit():
                reply_to = int(parts[-1])
        if not chat_id or not reply_to:
            raise ValueError("Missing discussion chat or message id for comment reply")

        await self.update_inbox_status(user_id, item["id"], "in_progress")
        base = (settings.TG_BOT_SERVICE_URL or "").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{base}/tg/reply",
                    json={
                        "user_id": user_id,
                        "chat_id": str(chat_id),
                        "reply_to_msg_id": int(reply_to),
                        "text": text,
                    },
                )
            if resp.status_code >= 400:
                detail = resp.text[:300]
                updated = await self.update_inbox_status(user_id, item["id"], "reply_failed")
                if updated:
                    updated["reply_error"] = detail
                    updated["reply_text"] = text
                return updated or item
            data = resp.json() if resp.content else {}
            updated = await self.update_inbox_status(user_id, item["id"], "replied")
            if updated:
                updated["reply_text"] = text
                updated["reply_queued"] = False
                updated["reply_status"] = "sent"
                updated["tg_reply"] = data
            return updated or item
        except Exception as exc:
            updated = await self.update_inbox_status(user_id, item["id"], "reply_failed")
            if updated:
                updated["reply_error"] = str(exc)
                updated["reply_text"] = text
            return updated or item

    async def get_inbox_item(self, user_id: int, item_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, brand_id, network, channel_id, thread_id,
                           type, author, text, status, created_at, external_msg_id, edited_text, meta
                    FROM smm_inbox_items WHERE id = %s AND user_id = %s
                    """,
                    (item_id, user_id),
                )
                row = await cur.fetchone()
                return _row_inbox(row) if row else None
        finally:
            await release_db_connection(conn)

    async def set_inbox_edited_text(
        self, user_id: int, item_id: int, edited_text: str
    ) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_inbox_items SET edited_text = %s
                    WHERE id = %s AND user_id = %s
                    RETURNING id, user_id, brand_id, network, channel_id, thread_id,
                              type, author, text, status, created_at, external_msg_id, edited_text, meta
                    """,
                    (edited_text, item_id, user_id),
                )
                row = await cur.fetchone()
                return _row_inbox(row) if row else None
        finally:
            await release_db_connection(conn)

    async def redirect_inbox(
        self,
        user_id: int,
        item_id: int,
        targets: list[dict],
        use_edited: bool = True,
        publish_at: Optional[str] = None,
        pending_approval: bool = False,
    ) -> dict:
        await ensure_smm_feature(user_id, "inbox_redirect")
        item = await self.get_inbox_item(user_id, item_id)
        if not item:
            raise ValueError("Inbox item not found")
        text = (item.get("edited_text") if use_edited and item.get("edited_text") else item.get("text")) or ""
        status = "pending_approval" if pending_approval else "ready"
        if pending_approval:
            await ensure_smm_feature(user_id, "approval_workflow")
        job = await self.create_job(
            user_id=user_id,
            brand_id=item.get("brand_id"),
            text=text,
            media=[],
            targets=targets,
            publish_at=publish_at,
            adapt=True,
            status=status,
        )
        return {"job": job, "inbox_item": item}

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
        adapter_overrides: Optional[dict] = None,
        charge_quota: bool = False,
    ) -> dict:
        media = media or []
        targets = targets or []
        tariff = await get_user_tariff(user_id)
        max_targets = plan_limit(tariff, "max_targets_per_job", 1)
        if len(targets) > max_targets:
            raise QuotaExceededError(
                resource="max_targets_per_job", limit=max_targets, used=len(targets)
            )
        if len(targets) > 1 and not plan_feature(tariff, "multi_channel_send", True):
            raise QuotaExceededError(
                resource="feature:multi_channel_send", limit=1, used=len(targets)
            )
        from services.platform_auth_service import PlatformAction, platform_auth_service

        if targets and status in ("ready", "scheduled", "publishing"):
            await platform_auth_service.require_targets_auth(
                user_id, targets, has_media=bool(media)
            )
        pub_at = None
        if publish_at:
            try:
                pub_at = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
            except ValueError:
                pub_at = None
            if pub_at:
                if not plan_feature(tariff, "schedule", True):
                    raise QuotaExceededError(
                        resource="feature:schedule", limit=0, used=0
                    )
                horizon = plan_limit(tariff, "schedule_horizon_days", 7)
                now = datetime.utcnow()
                pub_naive = pub_at.replace(tzinfo=None) if pub_at.tzinfo else pub_at
                if pub_naive > now + timedelta(days=horizon):
                    raise QuotaExceededError(
                        resource="schedule_horizon_days", limit=horizon, used=horizon + 1
                    )
        if pub_at and status == "ready":
            status = "scheduled"
        # Quota is charged on successful publish in execute_job (not at create)
        if charge_quota:
            units = max(1, len(targets)) if status != "draft" else 0
            if units:
                await ensure_monthly_post_quota(user_id, units=units)
        adapters = adapt_for_networks(text, media, targets) if adapt else {}
        if adapter_overrides:
            for net, payload in adapter_overrides.items():
                if not isinstance(payload, dict):
                    continue
                base = adapters.get(net) if isinstance(adapters.get(net), dict) else {}
                adapters[net] = {**base, **payload}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_publish_jobs
                        (user_id, brand_id, source_text, media, targets, adapters_result, publish_at, status)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                    RETURNING id, user_id, brand_id, source_text, media, targets, adapters_result,
                              publish_at, status, created_at, updated_at, retry_count, last_error
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
        await ensure_smm_feature(user_id, "automations")
        existing = await self.list_automations(user_id)
        await ensure_smm_limit(user_id, "max_automations", len(existing), units=1)
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

    async def analytics_overview(
        self,
        user_id: int,
        brand_id: Optional[int],
        period: str = "7d",
        channel_id: Optional[int] = None,
    ) -> dict:
        days = 7 if period == "7d" else (30 if period == "30d" else 7)
        since = datetime.utcnow() - timedelta(days=days)
        channel = await self.get_channel(user_id, channel_id) if channel_id else None
        if channel_id and not channel:
            return {
                "period": period,
                "brand_id": brand_id,
                "channel_id": channel_id,
                "reach": 0,
                "engagement": 0,
                "er": 0.0,
                "posts": 0,
                "subscriber_growth": 0,
                "by_network": {
                    "tg": {"views": 0, "likes": 0, "comments": 0, "reposts": 0, "posts": 0},
                    "vk": {"views": 0, "likes": 0, "comments": 0, "reposts": 0, "posts": 0},
                },
            }
        empty_row = (0, 0, 0, 0, 0)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                tg = empty_row
                vk = empty_row
                if channel is None or channel.get("network") == "tg":
                    where = "user_id = %s AND created_at >= %s AND status != 'deleted'"
                    params: list[Any] = [user_id, since]
                    if channel:
                        extra, extra_params = _posts_channel_where("tg", channel.get("external_id"))
                        where = f"{where} AND {extra}"
                        params.extend(extra_params)
                    await cur.execute(
                        f"""
                        SELECT COALESCE(SUM(views),0), COALESCE(SUM(likes),0),
                               COALESCE(SUM(comments),0), COALESCE(SUM(reposts),0), COUNT(*)
                        FROM tg_posts
                        WHERE {where}
                        """,
                        params,
                    )
                    tg = await cur.fetchone() or empty_row
                if channel is None or channel.get("network") == "vk":
                    where = "user_id = %s AND created_at >= %s AND status != 'deleted'"
                    params = [user_id, since]
                    if channel:
                        extra, extra_params = _posts_channel_where("vk", channel.get("external_id"))
                        where = f"{where} AND {extra}"
                        params.extend(extra_params)
                    await cur.execute(
                        f"""
                        SELECT COALESCE(SUM(views),0), COALESCE(SUM(likes),0),
                               COALESCE(SUM(comments),0), COALESCE(SUM(reposts),0), COUNT(*)
                        FROM vk_posts
                        WHERE {where}
                        """,
                        params,
                    )
                    vk = await cur.fetchone() or empty_row
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
                "channel_id": channel["id"] if channel else channel_id,
                "reach": total_views,
                "engagement": total_eng,
                "er": er,
                "posts": total_posts,
                "subscriber_growth": (
                    await self.analytics_growth(user_id, brand_id)
                ).get("subscriber_growth", 0),
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
        self,
        user_id: int,
        brand_id: Optional[int],
        sort: str = "er",
        limit: int = 20,
        channel_id: Optional[int] = None,
    ) -> list[dict]:
        channels = await self.list_all_channels(user_id, brand_id)
        if channel_id:
            channels = [c for c in channels if c.get("id") == channel_id]
            if not channels:
                return []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, post_text, views, likes, comments, reposts, 'tg' AS network,
                           created_at, post_date, publish_at, telegram_chat_id, domain, title,
                           target_channels
                    FROM tg_posts WHERE user_id = %s AND status != 'deleted'
                    UNION ALL
                    SELECT id, post_text, views, likes, comments, reposts, 'vk' AS network,
                           created_at, post_date, publish_at, NULL::text, domain, title,
                           target_groups
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
                network = r[6]
                created_at, post_date, publish_at = r[7], r[8], r[9]
                chat_ref, domain, title, targets = r[10], r[11], r[12], r[13]
                published_at = publish_at or post_date or created_at
                matched = _match_channel(channels, network, chat_ref, domain, targets)
                if channel_id and (not matched or matched.get("id") != channel_id):
                    continue
                fallback_tokens = _iter_channel_tokens(chat_ref) + _iter_channel_tokens(domain)
                channel_external = (
                    matched.get("external_id") if matched else (fallback_tokens[0] if fallback_tokens else None)
                )
                channel_title = None
                if matched:
                    channel_title = matched.get("title") or matched.get("external_id")
                else:
                    channel_title = title or domain or channel_external
                items.append(
                    {
                        "id": r[0],
                        "text": (r[1] or "")[:200],
                        "views": views,
                        "likes": int(r[3] or 0),
                        "comments": int(r[4] or 0),
                        "reposts": int(r[5] or 0),
                        "er": round(er, 2),
                        "network": network,
                        "created_at": _iso_dt(created_at),
                        "published_at": _iso_dt(published_at),
                        "channel_id": matched["id"] if matched else None,
                        "channel_external_id": str(channel_external) if channel_external else None,
                        "channel_title": channel_title,
                        "brand_id": brand_id,
                    }
                )
            key = "er" if sort == "er" else "views"
            items.sort(key=lambda x: x[key], reverse=True)
            return items[:limit]
        finally:
            await release_db_connection(conn)

    async def analytics_growth(self, user_id: int, brand_id: Optional[int]) -> dict:
        channels = await self.list_all_channels(user_id, brand_id)
        if not channels:
            return {"brand_id": brand_id, "points": [], "subscriber_growth": 0}
        channel_ids = [c["id"] for c in channels]
        since = datetime.utcnow() - timedelta(days=30)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT channel_id, subscribers, captured_at
                    FROM smm_channel_metric_snapshots
                    WHERE channel_id = ANY(%s) AND captured_at >= %s
                    ORDER BY captured_at ASC
                    """,
                    (channel_ids, since),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        by_day: dict[str, int] = {}
        for ch_id, subs, captured_at in rows:
            day_key = captured_at.date().isoformat() if captured_at else ""
            if day_key:
                by_day[day_key] = by_day.get(day_key, 0) + int(subs or 0)
        points = [{"date": d, "subscribers": v} for d, v in sorted(by_day.items())]
        growth = 0
        if len(points) >= 2:
            growth = points[-1]["subscribers"] - points[0]["subscribers"]
        return {"brand_id": brand_id, "points": points, "subscriber_growth": growth}

    async def analytics_messages(
        self,
        user_id: int,
        brand_id: Optional[int],
        period: str = "7d",
        channel_id: Optional[int] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Operational + engagement message list for Analytics tab."""
        days = 7 if period == "7d" else (30 if period == "30d" else 7)
        since = datetime.utcnow() - timedelta(days=days)
        posts = await self.analytics_posts(
            user_id, brand_id, sort="views", limit=limit, channel_id=channel_id
        )
        for p in posts:
            p["status"] = "published"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                where = "e.user_id = %s AND e.created_at >= %s"
                params: list[Any] = [user_id, since]
                if channel_id:
                    where += " AND e.channel_id = %s"
                    params.append(channel_id)
                elif brand_id:
                    await cur.execute(
                        "SELECT id FROM smm_brand_channels WHERE brand_id = %s",
                        (brand_id,),
                    )
                    ids = [r[0] for r in await cur.fetchall()]
                    if not ids:
                        return {"posts": posts, "events": []}
                    where += " AND e.channel_id = ANY(%s)"
                    params.append(ids)
                await cur.execute(
                    f"""
                    SELECT e.direction, e.platform, e.post_id, e.external_msg_id,
                           e.created_at, e.metadata, c.title, c.external_id
                    FROM smm_message_events e
                    LEFT JOIN smm_brand_channels c ON c.id = e.channel_id
                    WHERE {where}
                    ORDER BY e.created_at DESC
                    LIMIT %s
                    """,
                    (*params, limit),
                )
                event_rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        events = []
        for i, r in enumerate(event_rows):
            meta = r[5]
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except (json.JSONDecodeError, TypeError):
                    meta = {}
            events.append(
                {
                    "id": f"evt-{i}",
                    "direction": r[0],
                    "network": r[1],
                    "post_id": r[2],
                    "external_msg_id": r[3],
                    "created_at": _iso_dt(r[4]),
                    "channel_title": r[6] or r[7],
                    "text": meta.get("text_preview") if isinstance(meta, dict) else None,
                    "status": r[0],
                }
            )
        return {"posts": posts, "events": events}

    async def sync_competitor_snapshots(self, user_id: Optional[int] = None) -> dict:
        """Import recent competitor/source posts from platform tables into snapshots."""
        conn = await get_db_connection()
        inserted = 0
        try:
            async with conn.cursor() as cur:
                if user_id is not None:
                    await cur.execute(
                        """
                        SELECT c.id, c.network, c.external_id, b.user_id
                        FROM smm_brand_channels c
                        JOIN smm_brands b ON b.id = c.brand_id
                        WHERE b.user_id = %s AND c.role IN ('competitor', 'source')
                        """,
                        (user_id,),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT c.id, c.network, c.external_id, b.user_id
                        FROM smm_brand_channels c
                        JOIN smm_brands b ON b.id = c.brand_id
                        WHERE c.role IN ('competitor', 'source')
                        """
                    )
                channels = await cur.fetchall()
                for ch_id, network, external_id, uid in channels:
                    ext = str(external_id).strip()
                    if network == "vk":
                        await cur.execute(
                            """
                            SELECT vk_source_id, post_text, views, likes, comments, reposts, post_date
                            FROM vk_posts
                            WHERE user_id = %s AND domain = %s
                            ORDER BY post_date DESC NULLS LAST
                            LIMIT 20
                            """,
                            (uid, ext.lstrip("-")),
                        )
                    else:
                        await cur.execute(
                            """
                            SELECT id, post_text, views, likes, comments, reposts, post_date
                            FROM tg_posts
                            WHERE user_id = %s AND domain = %s
                            ORDER BY post_date DESC NULLS LAST
                            LIMIT 20
                            """,
                            (uid, ext),
                        )
                    for row in await cur.fetchall():
                        ext_post_id = str(row[0])
                        await cur.execute(
                            """
                            SELECT 1 FROM smm_competitor_snapshots
                            WHERE channel_id = %s AND external_post_id = %s
                            LIMIT 1
                            """,
                            (ch_id, ext_post_id),
                        )
                        if await cur.fetchone():
                            continue
                        await cur.execute(
                            """
                            INSERT INTO smm_competitor_snapshots
                                (channel_id, external_post_id, post_text, views, likes, comments, reposts, posted_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (ch_id, ext_post_id, row[1], row[2], row[3], row[4], row[5], row[6]),
                        )
                        inserted += 1
            return {"inserted": inserted, "channels": len(channels)}
        finally:
            await release_db_connection(conn)

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

    async def channel_stats(
        self, user_id: int, brand_id: Optional[int] = None, period: str = "7d"
    ) -> list[dict]:
        tariff = await get_user_tariff(user_id)
        max_days = plan_limit(tariff, "stats_retention_days", 7)
        days = 7 if period == "7d" else (30 if period == "30d" else (90 if period == "90d" else 7))
        days = min(days, max_days)
        since = (datetime.utcnow() - timedelta(days=days)).date()
        channels = await self.list_all_channels(user_id, brand_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                result = []
                for ch in channels:
                    await cur.execute(
                        """
                        SELECT COALESCE(SUM(sent),0), COALESCE(SUM(received),0),
                               COALESCE(SUM(failed),0), COALESCE(SUM(alerts_sent),0)
                        FROM smm_channel_counters
                        WHERE user_id = %s AND channel_id = %s AND day >= %s
                        """,
                        (user_id, ch["id"], since),
                    )
                    row = await cur.fetchone()
                    sent = int(row[0] or 0) if row else 0
                    received = int(row[1] or 0) if row else 0
                    failed = int(row[2] or 0) if row else 0
                    alerts_sent = int(row[3] or 0) if row else 0
                    # Fallback: count inbox received for channel
                    if received == 0:
                        await cur.execute(
                            """
                            SELECT COUNT(*) FROM smm_inbox_items
                            WHERE user_id = %s AND channel_id = %s AND created_at >= %s
                            """,
                            (user_id, ch["id"], datetime.utcnow() - timedelta(days=days)),
                        )
                        r2 = await cur.fetchone()
                        received = int(r2[0] or 0) if r2 else 0
                    result.append(
                        {
                            "channel_id": ch["id"],
                            "brand_id": ch["brand_id"],
                            "brand_name": ch.get("brand_name"),
                            "network": ch["network"],
                            "external_id": ch["external_id"],
                            "title": ch.get("title"),
                            "role": ch["role"],
                            "sent": sent,
                            "received": received,
                            "failed": failed,
                            "alerts_sent": alerts_sent,
                            "conversion_pct": round(
                                (sent / received * 100) if received else 0.0, 1
                            ),
                        }
                    )
                return result
        finally:
            await release_db_connection(conn)

    async def bump_channel_counter(
        self,
        user_id: int,
        channel_id: int,
        *,
        sent: int = 0,
        received: int = 0,
        failed: int = 0,
        alerts_sent: int = 0,
    ) -> None:
        day = datetime.utcnow().date()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_channel_counters
                        (user_id, channel_id, day, sent, received, failed, alerts_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (channel_id, day) DO UPDATE SET
                        sent = smm_channel_counters.sent + EXCLUDED.sent,
                        received = smm_channel_counters.received + EXCLUDED.received,
                        failed = smm_channel_counters.failed + EXCLUDED.failed,
                        alerts_sent = smm_channel_counters.alerts_sent + EXCLUDED.alerts_sent
                    """,
                    (user_id, channel_id, day, sent, received, failed, alerts_sent),
                )
        finally:
            await release_db_connection(conn)

    async def resolve_channel_by_external_id(
        self,
        user_id: int,
        network: str,
        external_id: str,
    ) -> Optional[dict]:
        """Match BrandChannel by network + external_id (Telegram/VK id formats)."""
        needle = str(external_id).strip()
        if not needle:
            return None
        needle_stripped = needle.lstrip("-")
        channels = await self.list_all_channels(user_id)
        for c in channels:
            if c.get("network") != network:
                continue
            ext = str(c.get("external_id") or "").strip()
            if not ext:
                continue
            if ext == needle or ext.lstrip("-") == needle_stripped:
                return c
            try:
                if int(ext) == int(needle):
                    return c
            except (TypeError, ValueError):
                pass
        return None

    async def record_message_event(
        self,
        user_id: int,
        channel_id: Optional[int],
        direction: str,
        platform: str,
        *,
        post_id: Optional[int] = None,
        external_msg_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        if direction not in ("collected", "published", "alert", "failed"):
            return
        if platform not in ("tg", "vk"):
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_message_events
                        (user_id, channel_id, direction, platform, post_id, external_msg_id, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        user_id,
                        channel_id,
                        direction,
                        platform,
                        post_id,
                        external_msg_id,
                        json.dumps(metadata or {}, ensure_ascii=False),
                    ),
                )
        finally:
            await release_db_connection(conn)

    async def bump_channel_from_collector(
        self,
        user_id: int,
        *,
        channel_id: Optional[int] = None,
        network: Optional[str] = None,
        external_id: Optional[str] = None,
        sent: int = 0,
        received: int = 0,
        failed: int = 0,
        alerts_sent: int = 0,
        direction: Optional[str] = None,
        platform: Optional[str] = None,
        post_id: Optional[int] = None,
        external_msg_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Resolve channel and bump counters; optionally record message event."""
        ch_id = channel_id
        if not ch_id and network and external_id:
            ch = await self.resolve_channel_by_external_id(user_id, network, external_id)
            ch_id = ch["id"] if ch else None
        if not ch_id:
            return False
        if sent or received or failed or alerts_sent:
            await self.bump_channel_counter(
                user_id,
                ch_id,
                sent=sent,
                received=received,
                failed=failed,
                alerts_sent=alerts_sent,
            )
        if direction and platform:
            await self.record_message_event(
                user_id,
                ch_id,
                direction,
                platform,
                post_id=post_id,
                external_msg_id=external_msg_id,
                metadata=metadata,
            )
        return True

    async def record_post_metric_snapshot(
        self,
        user_id: int,
        platform: str,
        post_id: int,
        *,
        views: int = 0,
        likes: int = 0,
        comments: int = 0,
        reposts: int = 0,
    ) -> None:
        if platform not in ("tg", "vk"):
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_post_metric_snapshots
                        (user_id, platform, post_id, views, likes, comments, reposts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, platform, post_id, views, likes, comments, reposts),
                )
        finally:
            await release_db_connection(conn)

    async def record_channel_subscriber_snapshot(
        self, channel_id: int, subscribers: int
    ) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_channel_metric_snapshots (channel_id, subscribers)
                    VALUES (%s, %s)
                    """,
                    (channel_id, max(0, int(subscribers))),
                )
        finally:
            await release_db_connection(conn)

    async def fetch_due_jobs(self, limit: int = 50) -> list[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, brand_id, source_text, media, targets, adapters_result,
                           publish_at, status, created_at, updated_at, retry_count, last_error
                    FROM smm_publish_jobs
                    WHERE status IN ('ready', 'scheduled')
                      AND (publish_at IS NULL OR publish_at <= NOW())
                    ORDER BY COALESCE(publish_at, created_at) ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
                return [_row_job(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def execute_job(self, job: dict) -> dict:
        """Materialize job into tg_posts / vk_posts per target; update adapters_result."""
        from services.post_service import post_service

        job_id = job["id"]
        user_id = job["user_id"]
        targets = job.get("targets") or []
        media = job.get("media") or []
        text = job.get("source_text") or ""
        adapters = job.get("adapters_result") or {}
        per_target: dict[str, Any] = (
            dict(adapters["targets"]) if isinstance(adapters.get("targets"), dict) else {}
        )

        channels = await self.list_all_channels(user_id)
        from services.platform_auth_service import PlatformAction, PlatformAuthError, platform_auth_service

        await self.update_job(user_id, job_id, status="publishing")
        ok = 0
        fail = 0
        for t in targets:
            network = t.get("network")
            external_id = str(t.get("external_id") or "")
            key = f"{network}:{external_id}"
            action = (
                PlatformAction.PUBLISH_MEDIA
                if media and network == "vk"
                else PlatformAction.PUBLISH_TEXT
            )
            try:
                await platform_auth_service.require_platform(user_id, str(network), action)
            except PlatformAuthError as auth_exc:
                per_target[key] = {"status": "failed", "error": auth_exc.message}
                fail += 1
                continue
            ch = next(
                (
                    c
                    for c in channels
                    if c["network"] == network and str(c["external_id"]) == external_id
                ),
                None,
            )
            if ch and ch.get("publish_enabled") is False:
                per_target[key] = {"status": "skipped", "error": "publish_enabled=false"}
                fail += 1
                continue
            try:
                await ensure_monthly_post_quota(user_id, units=1)
                if network == "tg":
                    tg_text = (adapters.get("tg") or {}).get("text", text)
                    await post_service.create_tg_post_record(
                        user_id=user_id,
                        text=tg_text,
                        images=media if media else None,
                        to_tg=True,
                        publish_at=None,
                        target_channels=[external_id] if external_id else None,
                        skip_quota=True,
                    )
                elif network == "vk":
                    vk_payload = adapters.get("vk") or {}
                    vk_text = vk_payload.get("text", re.sub(r"<[^>]+>", "", text))
                    await post_service.create_vk_post_record(
                        user_id=user_id,
                        text=vk_text,
                        images=media,
                        to_vk=True,
                        target_groups=[external_id] if external_id else None,
                        skip_quota=True,
                    )
                else:
                    raise ValueError(f"Unsupported network {network}")
                per_target[key] = {"status": "published"}
                ok += 1
                if ch:
                    await self.bump_channel_counter(user_id, ch["id"], sent=1)
            except Exception as exc:
                per_target[key] = {"status": "failed", "error": str(exc)}
                fail += 1
                if ch:
                    await self.bump_channel_counter(user_id, ch["id"], failed=1)

        adapters_out = {**adapters, "targets": per_target}
        if fail == 0:
            final = "published"
        elif ok == 0:
            final = "failed"
        else:
            final = "partial"
        tariff = await get_user_tariff(user_id)
        max_retry = 3 if tariff == "full" else (2 if tariff == "standard" else 0)
        retry = int(job.get("retry_count") or 0)
        last_error = None
        if final == "failed" and retry < max_retry:
            final = "ready"
            retry += 1
            last_error = "retry scheduled"
        updated = await self.update_job(
            user_id,
            job_id,
            status=final,
            adapters_result=adapters_out,
        )
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_publish_jobs
                    SET retry_count = %s, last_error = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (retry, last_error or (None if final != "failed" else "publish failed"), job_id),
                )
        finally:
            await release_db_connection(conn)
        return updated or job

    async def run_due_jobs(self, limit: int = 50) -> dict:
        jobs = await self.fetch_due_jobs(limit)
        results = []
        for job in jobs:
            try:
                results.append(await self.execute_job(job))
            except Exception as exc:
                results.append({"id": job["id"], "error": str(exc)})
        return {"processed": len(results), "jobs": results}

    async def ingest_inbox_item(self, user_id: int, data: dict) -> dict:
        """Idempotent ingest with optional external_msg_id dedup."""
        item_type = data.get("type") or data.get("item_type") or "comment"
        if item_type not in ("dm", "comment", "reaction"):
            item_type = "comment"
        meta = data.get("meta") or {}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                ext = data.get("external_msg_id")
                if ext:
                    await cur.execute(
                        """
                        SELECT id FROM smm_inbox_items
                        WHERE user_id = %s AND network = %s AND external_msg_id = %s
                        """,
                        (user_id, data["network"], ext),
                    )
                    existing = await cur.fetchone()
                    if existing:
                        item = await self.get_inbox_item(user_id, existing[0])
                        return item or {"id": existing[0], "deduped": True}
                await cur.execute(
                    """
                    INSERT INTO smm_inbox_items
                        (user_id, brand_id, network, channel_id, thread_id, type, author, text,
                         status, external_msg_id, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id, user_id, brand_id, network, channel_id, thread_id,
                              type, author, text, status, created_at, external_msg_id, edited_text, meta
                    """,
                    (
                        user_id,
                        data.get("brand_id"),
                        data["network"],
                        data.get("channel_id"),
                        data.get("thread_id"),
                        item_type,
                        data.get("author"),
                        data.get("text"),
                        data.get("status", "new"),
                        ext,
                        json.dumps(meta),
                    ),
                )
                row = await cur.fetchone()
                item = _row_inbox(row)
                if item.get("channel_id"):
                    await self.bump_channel_counter(user_id, item["channel_id"], received=1)
                return item
        finally:
            await release_db_connection(conn)

    async def resolve_collect_channel(
        self, user_id: int, network: str, external_id: str
    ) -> Optional[dict]:
        """Find brand channel with collect_enabled for ingest."""
        channels = await self.list_all_channels(user_id)
        ext = str(external_id).strip()
        for c in channels:
            if c["network"] != network:
                continue
            if str(c["external_id"]).strip() != ext:
                continue
            if c.get("collect_enabled") is False:
                continue
            return c
        for c in channels:
            if (
                c["network"] == network
                and str(c["external_id"]).strip() == ext
                and c.get("role") in ("own", "source")
            ):
                return c
        return None

    async def resolve_discussion_channel(
        self, user_id: int, network: str, discussion_id: str
    ) -> Optional[dict]:
        """Match message chat_id to brand channel.discussion_external_id."""
        channels = await self.list_all_channels(user_id)
        disc = str(discussion_id).strip()
        for c in channels:
            if c["network"] != network:
                continue
            linked = c.get("discussion_external_id")
            if not linked or str(linked).strip() != disc:
                continue
            # Bound discussion: collect when comments_collect_enabled (default on bind in UI)
            if c.get("comments_collect_enabled") is False:
                continue
            return c
        return None

    async def ingest_from_collector(
        self,
        user_id: int,
        network: str,
        external_id: str,
        text: str,
        author: Optional[str] = None,
        external_msg_id: Optional[str] = None,
        item_type: str = "comment",
        meta: Optional[dict] = None,
    ) -> Optional[dict]:
        meta = meta or {}
        # Comments from discussion chat: resolve by discussion_external_id
        if item_type == "comment":
            ch = await self.resolve_discussion_channel(user_id, network, external_id)
            if not ch:
                ch = await self.resolve_collect_channel(user_id, network, external_id)
            if not ch:
                return None
            return await self.ingest_inbox_item(
                user_id,
                {
                    "brand_id": ch["brand_id"],
                    "network": network,
                    "channel_id": ch["id"],
                    "thread_id": external_id,
                    "type": "comment",
                    "author": author,
                    "text": text or "",
                    "external_msg_id": external_msg_id,
                    "status": "new",
                    "meta": {
                        **meta,
                        "discussion_id": external_id,
                        "channel_external_id": ch["external_id"],
                    },
                },
            )
        if item_type not in ("dm", "reaction"):
            return None
        ch = await self.resolve_collect_channel(user_id, network, external_id)
        if not ch:
            return None
        return await self.ingest_inbox_item(
            user_id,
            {
                "brand_id": ch["brand_id"],
                "network": network,
                "channel_id": ch["id"],
                "thread_id": external_id,
                "type": item_type,
                "author": author,
                "text": text or "",
                "external_msg_id": external_msg_id,
                "status": "new",
                "meta": meta,
            },
        )

    async def approve_job(self, user_id: int, job_id: int) -> Optional[dict]:
        await ensure_smm_feature(user_id, "approval_workflow")
        return await self.update_job(user_id, job_id, status="ready")


smm_service = SmmService()

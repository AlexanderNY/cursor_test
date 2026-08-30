"""SMM layer: brands, inbox, publish jobs, automations, analytics."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_COMPETITOR_SYNC_INTERVAL_MIN = 60
COMPETITOR_DEFAULT_THEMES = [
    "продукт",
    "акция",
    "новость",
    "контент",
    "другое",
]


def _text_hash(text: str) -> Optional[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _period_since(period: str) -> datetime:
    raw = (period or "24h").strip().lower()
    now = datetime.utcnow()
    if raw in ("7d", "7day", "week"):
        return now - timedelta(days=7)
    if raw in ("30d", "30day", "month"):
        return now - timedelta(days=30)
    # default 24h
    return now - timedelta(hours=24)


def _competitor_sync_interval(processing: Any) -> int:
    raw = processing
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raw = {}
    if not isinstance(raw, dict):
        return DEFAULT_COMPETITOR_SYNC_INTERVAL_MIN
    try:
        val = int(raw.get("sync_interval_min") or DEFAULT_COMPETITOR_SYNC_INTERVAL_MIN)
    except (TypeError, ValueError):
        return DEFAULT_COMPETITOR_SYNC_INTERVAL_MIN
    return max(5, min(val, 24 * 60))


def _texts_stats(texts: list[str]) -> dict[str, Any]:
    lengths = [len(t) for t in texts if t]
    count = len(lengths)
    avg_len = round(sum(lengths) / count, 1) if count else 0.0
    return {
        "posts_count": count,
        "avg_length": avg_len,
        "posts_per_day": None,
    }


def _posts_stats(posts: list[dict]) -> dict[str, Any]:
    texts = [(p.get("text") or "") for p in posts]
    stats = _texts_stats(texts)
    return stats

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
from services.url_channel_sync import (
    ensure_curl_url_item,
    new_url_channel_external_id,
    remove_curl_url_item,
    get_curl_url_item,
    sync_url_channel_to_curl,
)
from services.smm_networks import (
    CANONICAL_NETWORKS,
    is_allowed_network,
    network_label,
    normalize_network,
    setup_url,
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

BRAND_SELECT = (
    "id, user_id, group_id, name, color, tone_of_voice, style_notes, "
    "prompt_snippets, is_demo, created_at, updated_at"
)

MAX_TONE_OF_VOICE = 500
MAX_STYLE_NOTES = 1000
MAX_PROMPT_SNIPPETS = 5
MAX_SNIPPET_TITLE = 80
MAX_SNIPPET_TEXT = 500


def _sanitize_prompt_snippets(raw: Any) -> list[dict[str, str]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw[:MAX_PROMPT_SNIPPETS]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:MAX_SNIPPET_TITLE]
        text = str(item.get("text") or "").strip()[:MAX_SNIPPET_TEXT]
        if not title and not text:
            continue
        out.append({"title": title or text[:40], "text": text or title})
    return out


def _row_brand(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "group_id": r[2],
        "name": r[3],
        "color": r[4],
        "tone_of_voice": r[5],
        "style_notes": r[6],
        "prompt_snippets": _sanitize_prompt_snippets(r[7]),
        "is_demo": bool(r[8]),
        "created_at": r[9].isoformat() if r[9] else None,
        "updated_at": r[10].isoformat() if r[10] else None,
    }


def compose_brand_voice(brand: Optional[dict[str, Any]]) -> Optional[str]:
    """Build tone string from brand TOV + style notes for AI calls."""
    if not brand:
        return None
    tov = str(brand.get("tone_of_voice") or "").strip()[:MAX_TONE_OF_VOICE]
    notes = str(brand.get("style_notes") or "").strip()[:MAX_STYLE_NOTES]
    parts: list[str] = []
    if tov:
        parts.append(tov)
    if notes:
        parts.append(notes)
    if not parts:
        return None
    combined = " · ".join(parts)
    # Soften injection-like phrases (same patterns as ai_assist_service)
    for pattern in (
        re.compile(r"(?i)\bsystem\s*:"),
        re.compile(r"(?i)\bassistant\s*:"),
        re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions"),
        re.compile(r"(?i)забыть\s+(все\s+)?(предыдущие\s+)?инструкции"),
    ):
        combined = pattern.sub("", combined)
    combined = combined.strip()
    return combined or None


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
        "assigned_to": None,
        "rejection_comment": None,
    }
    if len(r) > 11:
        out["retry_count"] = int(r[11] or 0)
    if len(r) > 12:
        out["last_error"] = r[12]
    if len(r) > 13:
        out["assigned_to"] = r[13]
    if len(r) > 14:
        out["rejection_comment"] = r[14]
    return out


JOB_COLUMNS = """
id, user_id, brand_id, source_text, media, targets, adapters_result,
publish_at, status, created_at, updated_at, retry_count, last_error,
assigned_to, rejection_comment
"""

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
    """Network adapters: TG keeps formatting; others get plain text variants."""
    networks = {normalize_network(t.get("network")) for t in targets}
    result: dict[str, Any] = {}
    plain = re.sub(r"<[^>]+>", "", text)
    plain = plain.replace("&nbsp;", " ").strip()
    if "tg" in networks:
        result["tg"] = {
            "text": text,
            "parse_mode": "HTML",
            "keep_spoiler": True,
            "media": media,
        }
    if "vk" in networks:
        result["vk"] = {
            "text": plain,
            "attachments_mode": "carousel" if len(media) > 1 else ("single" if media else "none"),
            "media": media,
            "poll_hint": False,
        }
    for net in ("instagram", "threads", "tw", "dzen", "wp"):
        if net not in networks:
            continue
        result[net] = {
            "text": plain,
            "media": media,
        }
    return result


class SmmService:
    async def list_brands(self, user_id: int) -> list[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {BRAND_SELECT}
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
        tone_of_voice: Optional[str] = None,
        style_notes: Optional[str] = None,
        prompt_snippets: Optional[list] = None,
    ) -> dict:
        if not _HEX_RE.match(color):
            color = BRAND_PALETTE[0]
        brands = await self.list_brands(user_id)
        await ensure_smm_limit(user_id, "max_brands", len(brands), units=1)
        tov = (tone_of_voice or "").strip()[:MAX_TONE_OF_VOICE] or None
        notes = (style_notes or "").strip()[:MAX_STYLE_NOTES] or None
        snippets = _sanitize_prompt_snippets(prompt_snippets)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    INSERT INTO smm_brands (
                        user_id, group_id, name, color,
                        tone_of_voice, style_notes, prompt_snippets
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING {BRAND_SELECT}
                    """,
                    (
                        user_id,
                        group_id,
                        name.strip(),
                        color,
                        tov,
                        notes,
                        json.dumps(snippets, ensure_ascii=False),
                    ),
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
                    f"""
                    SELECT {BRAND_SELECT}
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
        tone_of_voice: Optional[str] = None,
        style_notes: Optional[str] = None,
        prompt_snippets: Optional[list] = None,
        *,
        clear_tone_of_voice: bool = False,
        clear_style_notes: bool = False,
    ) -> Optional[dict]:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return None
        new_name = name.strip() if name else brand["name"]
        new_color = color if color and _HEX_RE.match(color) else brand["color"]
        new_group = group_id if group_id is not None else brand["group_id"]
        if clear_tone_of_voice:
            new_tov = None
        elif tone_of_voice is not None:
            new_tov = tone_of_voice.strip()[:MAX_TONE_OF_VOICE] or None
        else:
            new_tov = brand.get("tone_of_voice")
        if clear_style_notes:
            new_notes = None
        elif style_notes is not None:
            new_notes = style_notes.strip()[:MAX_STYLE_NOTES] or None
        else:
            new_notes = brand.get("style_notes")
        if prompt_snippets is not None:
            new_snippets = _sanitize_prompt_snippets(prompt_snippets)
        else:
            new_snippets = brand.get("prompt_snippets") or []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_brands
                    SET name = %s, color = %s, group_id = %s,
                        tone_of_voice = %s, style_notes = %s,
                        prompt_snippets = %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING {BRAND_SELECT}
                    """,
                    (
                        new_name,
                        new_color,
                        new_group,
                        new_tov,
                        new_notes,
                        json.dumps(new_snippets, ensure_ascii=False),
                        brand_id,
                        user_id,
                    ),
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
        external_id: str = "",
        title: Optional[str] = None,
        kind: str = "channel",
        role: str = "own",
        color_override: Optional[str] = None,
        initial_url: Optional[str] = None,
    ) -> dict:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        network = normalize_network(network)
        if not is_allowed_network(network):
            raise ValueError(
                "network must be one of: "
                + ", ".join(sorted(CANONICAL_NETWORKS))
            )
        if role not in ("own", "competitor", "source"):
            raise ValueError("invalid role")
        if kind not in ("channel", "group", "public"):
            raise ValueError("invalid kind")

        # URL radar: source (content collect) or competitor (monitoring)
        if network == "url":
            if role not in ("source", "competitor"):
                role = "source"
            kind = "public"
            if role == "competitor":
                await ensure_smm_feature(user_id, "competitors")
            ext = new_url_channel_external_id()
            page_url = (initial_url or "").strip()
            if not page_url and title and str(title).strip().lower().startswith(("http://", "https://")):
                page_url = str(title).strip()
            if not page_url and external_id and str(external_id).strip().lower().startswith(("http://", "https://")):
                page_url = str(external_id).strip()
            if not page_url:
                raise ValueError("Укажите URL страницы для сбора")
            display_title = (title or "").strip()
            if not display_title or display_title.lower().startswith(("http://", "https://")):
                try:
                    host = urlparse(page_url).netloc or page_url
                    display_title = host.replace("www.", "") or page_url
                except Exception:
                    display_title = page_url
            title = display_title
            await ensure_curl_url_item(user_id, ext, title, initial_url=page_url)
        else:
            ext = str(external_id or "").strip()
            if not ext:
                raise ValueError("Укажите ID канала")
            if network == "vk":
                from services.vk_helpers import parse_vk_group_id

                parsed_gid = parse_vk_group_id(ext)
                if parsed_gid is not None:
                    ext = str(parsed_gid)
            if role == "own":
                count = await self.count_own_channels(user_id)
                await ensure_smm_limit(user_id, "max_own_channels", count, units=1)
            if role == "competitor":
                await ensure_smm_feature(user_id, "competitors")
            # Selenium / OAuth platforms: default kind for public pages
            if network in ("instagram", "threads", "tw", "dzen", "wp") and kind == "channel":
                kind = "public"

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
            if not same and network == "vk":
                from services.vk_helpers import parse_vk_group_id

                a = parse_vk_group_id(other)
                b = parse_vk_group_id(ext)
                same = a is not None and a == b
            if same:
                raise ValueError(
                    f"Канал уже добавлен: «{ch.get('title') or other}» "
                    f"({network}/{other}, роль {ch.get('role')}). "
                    f"Откройте его в списке или удалите перед повторным добавлением."
                )

        from services.platform_auth_service import platform_auth_service

        # Soft probe: channels can always be created; ownership required only for publish.
        # VK competitor/source: verify read access via user OAuth.
        auth_probe: dict[str, Any] = {
            "auth_status": "unknown",
            "auth_error": None,
            "auth_capabilities": {},
            "auth_checked_at": datetime.utcnow(),
        }
        if network == "url" or (role == "competitor" and network != "vk"):
            auth_probe["auth_status"] = "not_required"
        else:
            auth_probe = await platform_auth_service.probe_channel_access(
                user_id, network, ext, role, strict=False
            )
            resolved = auth_probe.get("resolved_external_id")
            if network == "vk" and resolved:
                ext = str(resolved)

        is_owned = auth_probe.get("auth_status") == "connected"
        publish_enabled = role == "own" and is_owned
        collect_enabled = False if network == "url" else role in ("source", "own", "competitor")
        if network == "vk" and role == "competitor":
            collect_enabled = bool(
                (auth_probe.get("auth_capabilities") or {}).get("can_collect")
            ) or is_owned
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
                            publish_enabled,
                            collect_enabled,
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
                    if "check" in msg or "нарушает ограничение-проверку" in str(exc) or "checkviolation" in type(exc).__name__.lower():
                        raise ValueError(
                            f"Сеть '{network}' не разрешена схемой БД. "
                            "Примените deploy/sql/patch_smm_channels_all_networks.sql"
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
                if ch.get("network") == "url":
                    item = await get_curl_url_item(user_id, str(ch.get("external_id") or ""))
                    ch["url_config"] = item
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
        from services.demo_seed_service import is_demo_external_id

        url_config = fields.pop("url_config", None)

        # Demo / учебный контур: publish всегда выключен
        if brand.get("is_demo") or is_demo_external_id(existing.get("external_id")):
            if fields.get("publish_enabled") is True:
                fields["publish_enabled"] = False
            if fields.get("collect_enabled") is True:
                fields["collect_enabled"] = False

        # URL channels: never enable SMM publish_enabled (publish targets only)
        if existing.get("network") == "url":
            fields.pop("external_id", None)
            if fields.get("role") not in (None, "source", "competitor"):
                fields["role"] = "source"
            if fields.get("role") == "competitor":
                await ensure_smm_feature(user_id, "competitors")
            if fields.get("publish_enabled") is True:
                fields["publish_enabled"] = False
            # Competitor URL radar may use alert_enabled; sources keep alerts off
            if existing.get("role") != "competitor" and fields.get("role") != "competitor":
                if fields.get("alert_enabled") is True:
                    fields["alert_enabled"] = False

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
        if existing.get("network") != "url" and ("external_id" in fields or "role" in fields):
            updates.append("auth_status = %s")
            params.append("unknown")
            updates.append("auth_checked_at = NULL")
            updates.append("auth_error = NULL")

        ch: Optional[dict] = None
        if updates:
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
                    if ch and existing.get("network") != "url" and (
                        "external_id" in fields or "role" in fields
                    ):
                        probe = await platform_auth_service.probe_channel_access(
                            user_id,
                            ch["network"],
                            ch["external_id"],
                            ch.get("role") or "own",
                            strict=False,
                        )
                        await platform_auth_service.persist_channel_auth(channel_id, probe)
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
            finally:
                await release_db_connection(conn)

        refreshed = await self.get_channel(user_id, channel_id)
        if not refreshed:
            return ch

        if refreshed.get("network") == "url" and (
            url_config is not None
            or "publish_targets" in fields
            or "collect_enabled" in fields
            or "title" in fields
        ):
            brand_channels = await self.list_channels(user_id, brand_id)
            all_user = await self.list_all_channels(user_id)
            any_collect = any(
                c.get("network") == "url" and c.get("collect_enabled") for c in all_user
            )
            item = await sync_url_channel_to_curl(
                user_id,
                refreshed,
                url_config=url_config if isinstance(url_config, dict) else None,
                brand_channels=brand_channels,
                any_url_collect_enabled=any_collect,
            )
            refreshed["url_config"] = item

        return refreshed

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
                # Attach url_config for URL channels (review flag / display)
                for ch in result:
                    if ch.get("network") == "url":
                        item = await get_curl_url_item(
                            user_id, str(ch.get("external_id") or "")
                        )
                        ch["url_config"] = item
                return result
        finally:
            await release_db_connection(conn)

    def _serialize_channel_export(
        self,
        ch: dict[str, Any],
        id_to_channel: dict[int, dict[str, Any]],
    ) -> dict[str, Any]:
        """Portable channel payload: settings + target refs (network/external_id), no DB ids."""

        def _refs(ids: Any) -> list[dict[str, str]]:
            out: list[dict[str, str]] = []
            if not isinstance(ids, list):
                return out
            for raw in ids:
                try:
                    cid = int(raw)
                except (TypeError, ValueError):
                    continue
                target = id_to_channel.get(cid)
                if not target:
                    continue
                ext = str(target.get("external_id") or "").strip()
                net = str(target.get("network") or "").strip()
                if not ext or not net or net == "url":
                    continue
                out.append(
                    {
                        "network": net,
                        "external_id": ext,
                        "title": str(target.get("title") or "") or None,
                    }
                )
            return out

        delivery = ch.get("alert_delivery") if isinstance(ch.get("alert_delivery"), dict) else {}
        alert_target_ids = delivery.get("alert_targets") if isinstance(delivery, dict) else None
        alert_refs = _refs(alert_target_ids)
        # Legacy single channel_to_post → also as ref if we can match
        if not alert_refs and delivery.get("channel_to_post"):
            token = str(delivery.get("channel_to_post") or "").strip()
            for t in id_to_channel.values():
                if t.get("network") != "tg":
                    continue
                if _channel_id_equal(str(t.get("external_id") or ""), token):
                    alert_refs.append(
                        {
                            "network": "tg",
                            "external_id": str(t.get("external_id")),
                            "title": str(t.get("title") or "") or None,
                        }
                    )
                    break

        item: dict[str, Any] = {
            "network": ch.get("network"),
            "external_id": ch.get("external_id"),
            "title": ch.get("title"),
            "kind": ch.get("kind") or "channel",
            "role": ch.get("role") or "source",
            "brand_name": ch.get("brand_name"),
            "color_override": ch.get("color_override"),
            "publish_enabled": bool(ch.get("publish_enabled")),
            "collect_enabled": bool(ch.get("collect_enabled")),
            "alert_enabled": bool(ch.get("alert_enabled")),
            "comments_collect_enabled": bool(ch.get("comments_collect_enabled")),
            "discussion_external_id": ch.get("discussion_external_id"),
            "discussion_title": ch.get("discussion_title"),
            "save_conditions": ch.get("save_conditions") or [],
            "conditions_mode": ch.get("conditions_mode") or "any_of",
            "processing": ch.get("processing") or {},
            "publish_target_refs": _refs(ch.get("publish_targets")),
            "alert_rules": ch.get("alert_rules") or [],
            "alert_delivery": {
                "alert_text": (delivery or {}).get("alert_text"),
                "include_ai_summary": bool((delivery or {}).get("include_ai_summary")),
                "alert_target_refs": alert_refs,
            },
        }
        if ch.get("network") == "url":
            url_cfg = ch.get("url_config") if isinstance(ch.get("url_config"), dict) else {}
            item["external_id"] = None  # regenerated on create
            item["url_config"] = {
                k: url_cfg.get(k)
                for k in (
                    "url",
                    "xpath",
                    "schedule_time",
                    "run_once",
                    "take_screenshot",
                    "screenshot_format",
                    "process_before_publish",
                    "process_description",
                    "remove_emojis",
                    "remove_images",
                    "clean_html",
                    "process_services",
                    "status_review_after_process",
                    "add_static_html",
                    "static_html_content",
                    "screenshot_only",
                    "target_channels",
                    "target_groups",
                    "target_social_networks",
                )
                if url_cfg.get(k) is not None
            }
        return item

    async def export_channels(
        self,
        user_id: int,
        brand_id: Optional[int] = None,
    ) -> dict[str, Any]:
        channels = await self.list_all_channels(user_id, brand_id)
        # Enrich URL configs
        enriched: list[dict[str, Any]] = []
        for ch in channels:
            if ch.get("network") == "url":
                full = await self.get_channel(user_id, int(ch["id"]))
                enriched.append(full or ch)
            else:
                enriched.append(ch)
        id_map = {int(c["id"]): c for c in enriched if c.get("id") is not None}
        from datetime import datetime, timezone

        return {
            "format": "copyparse.channels",
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "brand_id": brand_id,
            "channels": [self._serialize_channel_export(c, id_map) for c in enriched],
        }

    def _find_channel_for_import(
        self,
        existing: list[dict[str, Any]],
        network: str,
        external_id: str,
        url: str = "",
    ) -> Optional[dict[str, Any]]:
        network = normalize_network(network)
        for ch in existing:
            if ch.get("network") != network:
                continue
            if network == "url":
                cfg = ch.get("url_config") if isinstance(ch.get("url_config"), dict) else {}
                other_url = str(cfg.get("url") or "").strip().rstrip("/").lower()
                want = (url or "").strip().rstrip("/").lower()
                if want and other_url and want == other_url:
                    return ch
                continue
            other = str(ch.get("external_id") or "").strip()
            if _channel_id_equal(other, external_id):
                return ch
            if network == "vk":
                from services.vk_helpers import parse_vk_group_id

                a = parse_vk_group_id(other)
                b = parse_vk_group_id(external_id)
                if a is not None and a == b:
                    return ch
        return None

    def _resolve_target_refs(
        self,
        refs: Any,
        brand_channels: list[dict[str, Any]],
    ) -> list[int]:
        if not isinstance(refs, list):
            return []
        ids: list[int] = []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            net = normalize_network(ref.get("network") or "")
            ext = str(ref.get("external_id") or "").strip()
            if not net or not ext:
                continue
            for ch in brand_channels:
                if ch.get("network") != net:
                    continue
                if _channel_id_equal(str(ch.get("external_id") or ""), ext):
                    ids.append(int(ch["id"]))
                    break
                if net == "vk":
                    from services.vk_helpers import parse_vk_group_id

                    a = parse_vk_group_id(str(ch.get("external_id") or ""))
                    b = parse_vk_group_id(ext)
                    if a is not None and a == b:
                        ids.append(int(ch["id"]))
                        break
        # unique preserve order
        seen: set[int] = set()
        out: list[int] = []
        for i in ids:
            if i not in seen:
                seen.add(i)
                out.append(i)
        return out

    async def import_channels(
        self,
        user_id: int,
        brand_id: int,
        payload: dict[str, Any],
        *,
        update_existing: bool = True,
    ) -> dict[str, Any]:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")

        raw_list = payload.get("channels") if isinstance(payload, dict) else None
        if not isinstance(raw_list, list):
            raise ValueError("Ожидается JSON с массивом channels")

        created = 0
        updated = 0
        skipped = 0
        errors: list[dict[str, Any]] = []
        warnings: list[str] = []

        # Pass 1: create / update identity + flow settings (targets later)
        for idx, raw in enumerate(raw_list):
            if not isinstance(raw, dict):
                errors.append({"index": idx, "error": "item must be an object"})
                continue
            try:
                network = normalize_network(raw.get("network") or "")
                if not is_allowed_network(network):
                    raise ValueError(f"unsupported network: {raw.get('network')}")
                role = str(raw.get("role") or "source").strip() or "source"
                kind = str(raw.get("kind") or "channel").strip() or "channel"
                title = (raw.get("title") or None) and str(raw.get("title")).strip()
                external_id = str(raw.get("external_id") or "").strip()
                url_cfg = raw.get("url_config") if isinstance(raw.get("url_config"), dict) else {}
                page_url = str(url_cfg.get("url") or "").strip()

                existing_list = await self.list_channels(user_id, brand_id)
                # enrich url for matching
                for ch in existing_list:
                    if ch.get("network") == "url" and "url_config" not in ch:
                        full = await self.get_channel(user_id, int(ch["id"]))
                        if full:
                            ch["url_config"] = full.get("url_config")

                match = self._find_channel_for_import(
                    existing_list, network, external_id, url=page_url
                )

                if match and not update_existing:
                    skipped += 1
                    continue

                if not match:
                    ch = await self.add_channel(
                        user_id,
                        brand_id,
                        network=network,
                        external_id=external_id if network != "url" else "",
                        title=title,
                        kind=kind,
                        role=role,
                        color_override=raw.get("color_override"),
                        initial_url=page_url if network == "url" else None,
                    )
                    created += 1
                else:
                    ch = match
                    updated += 1

                channel_id = int(ch["id"])
                settings: dict[str, Any] = {
                    "title": title if title is not None else ch.get("title"),
                    "kind": kind,
                    "role": role,
                    "color_override": raw.get("color_override"),
                    "discussion_external_id": raw.get("discussion_external_id"),
                    "discussion_title": raw.get("discussion_title"),
                    "comments_collect_enabled": bool(raw.get("comments_collect_enabled")),
                    "save_conditions": raw.get("save_conditions")
                    if isinstance(raw.get("save_conditions"), list)
                    else [],
                    "conditions_mode": raw.get("conditions_mode") or "any_of",
                    "processing": raw.get("processing")
                    if isinstance(raw.get("processing"), dict)
                    else {},
                    "alert_rules": raw.get("alert_rules")
                    if isinstance(raw.get("alert_rules"), list)
                    else [],
                }
                # Flags may fail auth — try soft
                for flag in ("collect_enabled", "alert_enabled", "publish_enabled"):
                    if flag in raw:
                        settings[flag] = bool(raw.get(flag))

                if network == "url" and url_cfg:
                    settings["url_config"] = url_cfg

                # Strip delivery targets for pass 1 (ids unknown / stale)
                delivery_in = (
                    raw.get("alert_delivery")
                    if isinstance(raw.get("alert_delivery"), dict)
                    else {}
                )
                settings["alert_delivery"] = {
                    "alert_text": delivery_in.get("alert_text"),
                    "include_ai_summary": bool(delivery_in.get("include_ai_summary")),
                    "alert_targets": [],
                    "channel_to_post": None,
                    "channel_to_post_title": None,
                }

                try:
                    await self.update_channel(user_id, brand_id, channel_id, **settings)
                except Exception as flag_exc:
                    # Retry without auth-gated flags
                    soft = {
                        k: v
                        for k, v in settings.items()
                        if k
                        not in ("collect_enabled", "alert_enabled", "publish_enabled")
                    }
                    soft["collect_enabled"] = False
                    soft["alert_enabled"] = False
                    soft["publish_enabled"] = False
                    await self.update_channel(user_id, brand_id, channel_id, **soft)
                    warnings.append(
                        f"{network}/{external_id or page_url or title}: "
                        f"настройки без Collect/Alert/Publish — {flag_exc}"
                    )
            except Exception as exc:
                errors.append(
                    {
                        "index": idx,
                        "network": raw.get("network"),
                        "external_id": raw.get("external_id"),
                        "error": str(exc),
                    }
                )

        # Pass 2: resolve publish/alert target refs within brand
        brand_channels = await self.list_channels(user_id, brand_id)
        for idx, raw in enumerate(raw_list):
            if not isinstance(raw, dict):
                continue
            try:
                network = normalize_network(raw.get("network") or "")
                external_id = str(raw.get("external_id") or "").strip()
                url_cfg = raw.get("url_config") if isinstance(raw.get("url_config"), dict) else {}
                page_url = str(url_cfg.get("url") or "").strip()
                # refresh url_config on brand_channels for matching
                for ch in brand_channels:
                    if ch.get("network") == "url" and "url_config" not in ch:
                        full = await self.get_channel(user_id, int(ch["id"]))
                        if full:
                            ch["url_config"] = full.get("url_config")
                match = self._find_channel_for_import(
                    brand_channels, network, external_id, url=page_url
                )
                if not match:
                    continue
                pub_ids = self._resolve_target_refs(
                    raw.get("publish_target_refs"), brand_channels
                )
                delivery_in = (
                    raw.get("alert_delivery")
                    if isinstance(raw.get("alert_delivery"), dict)
                    else {}
                )
                alert_ids = self._resolve_target_refs(
                    delivery_in.get("alert_target_refs"), brand_channels
                )
                first = next((c for c in brand_channels if int(c["id"]) in alert_ids), None)
                patch: dict[str, Any] = {
                    "publish_targets": pub_ids,
                    "alert_delivery": {
                        "alert_text": delivery_in.get("alert_text"),
                        "include_ai_summary": bool(delivery_in.get("include_ai_summary")),
                        "alert_targets": alert_ids,
                        "channel_to_post": (
                            str(first.get("external_id")) if first else None
                        ),
                        "channel_to_post_title": (
                            first.get("title") if first else None
                        ),
                    },
                }
                # Re-apply flags if present (may still fail)
                for flag in ("collect_enabled", "alert_enabled"):
                    if flag in raw:
                        patch[flag] = bool(raw.get(flag))
                try:
                    await self.update_channel(
                        user_id, brand_id, int(match["id"]), **patch
                    )
                except Exception as exc:
                    soft_patch = {
                        "publish_targets": pub_ids,
                        "alert_delivery": patch["alert_delivery"],
                    }
                    await self.update_channel(
                        user_id, brand_id, int(match["id"]), **soft_patch
                    )
                    warnings.append(
                        f"targets ok, flags skipped for #{match['id']}: {exc}"
                    )
            except Exception as exc:
                warnings.append(f"pass2 index {idx}: {exc}")

        return {
            "ok": len(errors) == 0,
            "created": created,
            "updated": updated if update_existing else 0,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings,
            "total": len(raw_list),
            "validation": await self.validate_brand_channels(
                user_id, brand_id, recheck_auth=True
            ),
        }

    async def validate_brand_channels(
        self,
        user_id: int,
        brand_id: int,
        *,
        recheck_auth: bool = True,
        channel_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        """Recheck access + config sanity for brand channels after import or on demand."""
        from services.platform_auth_service import platform_auth_service

        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")

        channels = await self.list_channels(user_id, brand_id)
        # Enrich URL configs for checks
        enriched: list[dict[str, Any]] = []
        for ch in channels:
            if channel_ids is not None and int(ch["id"]) not in channel_ids:
                continue
            if ch.get("network") == "url":
                full = await self.get_channel(user_id, int(ch["id"]))
                enriched.append(full or ch)
            else:
                enriched.append(ch)

        by_id = {int(c["id"]): c for c in enriched}
        issues: list[dict[str, Any]] = []
        checked = 0
        accessible = 0

        def _issue(
            ch: dict[str, Any],
            *,
            severity: str,
            code: str,
            message: str,
        ) -> None:
            issues.append(
                {
                    "channel_id": int(ch["id"]),
                    "network": ch.get("network"),
                    "external_id": ch.get("external_id"),
                    "title": ch.get("title"),
                    "role": ch.get("role"),
                    "severity": severity,
                    "code": code,
                    "message": message,
                }
            )

        # Pass A: live auth recheck for every channel
        for i, ch in enumerate(list(enriched)):
            checked += 1
            cid = int(ch["id"])
            network = normalize_network(ch.get("network") or "")
            if recheck_auth:
                try:
                    refreshed = await platform_auth_service.recheck_channel_auth(
                        user_id, cid
                    )
                    if refreshed:
                        enriched[i] = refreshed
                        by_id[cid] = refreshed
                        ch = refreshed
                except Exception as exc:
                    _issue(
                        ch,
                        severity="error",
                        code="recheck_failed",
                        message=f"Recheck не выполнен: {exc}",
                    )

            auth_status = ch.get("auth_status") or "unknown"
            if network == "url" or auth_status in ("connected", "not_required"):
                accessible += 1

        # Pass B: config + accessibility vs flags
        for ch in enriched:
            cid = int(ch["id"])
            network = normalize_network(ch.get("network") or "")
            role = str(ch.get("role") or "source")
            ext = str(ch.get("external_id") or "").strip()
            auth_status = ch.get("auth_status") or "unknown"
            caps: dict[str, Any] = (
                ch.get("auth_capabilities")
                if isinstance(ch.get("auth_capabilities"), dict)
                else {}
            )

            if network == "url":
                url_cfg = ch.get("url_config") if isinstance(ch.get("url_config"), dict) else {}
                page_url = str(url_cfg.get("url") or "").strip()
                if not page_url:
                    _issue(
                        ch,
                        severity="error",
                        code="url_missing",
                        message="URL-канал без адреса страницы (url_config.url)",
                    )
            elif not ext:
                _issue(
                    ch,
                    severity="error",
                    code="external_id_missing",
                    message="Не указан external_id канала",
                )

            if network != "url" and auth_status in (
                "missing",
                "invalid",
                "pending",
                "unknown",
            ):
                _issue(
                    ch,
                    severity="error" if role in ("own", "source") else "warning",
                    code="not_accessible",
                    message=(
                        ch.get("auth_error")
                        or f"Канал недоступен (auth={auth_status}). "
                        "Проверьте авторизацию платформы и Recheck."
                    ),
                )

            if ch.get("collect_enabled"):
                if network in ("tg", "vk") and not caps.get("can_collect", False):
                    _issue(
                        ch,
                        severity="error",
                        code="collect_without_auth",
                        message=(
                            "Collect включён, но нет права чтения "
                            f"({'user OAuth' if network == 'vk' else 'сессия Telegram'})."
                        ),
                    )
            if ch.get("alert_enabled"):
                if network == "url":
                    _issue(
                        ch,
                        severity="warning",
                        code="alert_on_url",
                        message="Алерты для URL обычно недоступны",
                    )
                elif network in ("tg", "vk") and not (
                    caps.get("can_alert", False) or caps.get("can_collect", False)
                ):
                    _issue(
                        ch,
                        severity="error",
                        code="alert_without_auth",
                        message="Alert включён, но нет сессии для чтения источника",
                    )
                delivery = (
                    ch.get("alert_delivery")
                    if isinstance(ch.get("alert_delivery"), dict)
                    else {}
                )
                if not (delivery.get("alert_text") or "").strip():
                    _issue(
                        ch,
                        severity="warning",
                        code="alert_text_empty",
                        message="Alert включён, но пустой alert_text",
                    )
                rules = ch.get("alert_rules") if isinstance(ch.get("alert_rules"), list) else []
                active_rules = [
                    r
                    for r in rules
                    if isinstance(r, dict)
                    and r.get("enabled", True)
                    and any(
                        isinstance(c, str) and c.strip()
                        for c in (r.get("save_conditions") or [])
                    )
                ]
                if not active_rules:
                    _issue(
                        ch,
                        severity="warning",
                        code="alert_rules_empty",
                        message="Alert включён, но нет правил с ключевыми словами",
                    )
                alert_targets = delivery.get("alert_targets") or []
                if not alert_targets and not delivery.get("channel_to_post"):
                    _issue(
                        ch,
                        severity="error",
                        code="alert_targets_missing",
                        message="Alert включён, но не указаны каналы доставки",
                    )

            if ch.get("publish_enabled") and role == "own":
                if auth_status != "connected":
                    _issue(
                        ch,
                        severity="error",
                        code="publish_without_ownership",
                        message="Publish включён, но собственность канала не подтверждена",
                    )
                elif caps and caps.get("can_publish_text") is False:
                    _issue(
                        ch,
                        severity="warning",
                        code="publish_capability_missing",
                        message="Publish включён, но can_publish_text=false после probe",
                    )

            pub_targets = (
                ch.get("publish_targets") if isinstance(ch.get("publish_targets"), list) else []
            )
            for tid in pub_targets:
                try:
                    tid_i = int(tid)
                except (TypeError, ValueError):
                    _issue(
                        ch,
                        severity="error",
                        code="publish_target_invalid",
                        message=f"Некорректный publish_target id: {tid}",
                    )
                    continue
                target = by_id.get(tid_i)
                if not target:
                    target = await self.get_channel(user_id, tid_i)
                    if target and int(target.get("brand_id") or 0) != brand_id:
                        target = None
                if not target:
                    _issue(
                        ch,
                        severity="error",
                        code="publish_target_missing",
                        message=f"publish_target #{tid_i} не найден в бренде",
                    )
                    continue
                if target.get("role") != "own":
                    _issue(
                        ch,
                        severity="warning",
                        code="publish_target_not_own",
                        message=(
                            f"Цель публикации #{tid_i} "
                            f"({target.get('network')}/{target.get('external_id')}) не role=own"
                        ),
                    )
                if target.get("auth_status") in ("missing", "invalid"):
                    _issue(
                        ch,
                        severity="warning",
                        code="publish_target_auth",
                        message=(
                            f"Цель #{tid_i} недоступна (auth={target.get('auth_status')})"
                        ),
                    )

            delivery = (
                ch.get("alert_delivery")
                if isinstance(ch.get("alert_delivery"), dict)
                else {}
            )
            for tid in delivery.get("alert_targets") or []:
                try:
                    tid_i = int(tid)
                except (TypeError, ValueError):
                    continue
                target = by_id.get(tid_i) or await self.get_channel(user_id, tid_i)
                if not target or int(target.get("brand_id") or 0) != brand_id:
                    _issue(
                        ch,
                        severity="error",
                        code="alert_target_missing",
                        message=f"alert_target #{tid_i} не найден в бренде",
                    )
                    continue
                if target.get("role") != "own":
                    _issue(
                        ch,
                        severity="warning",
                        code="alert_target_not_own",
                        message=f"alert_target #{tid_i} не role=own",
                    )
                if target.get("network") not in ("tg", "vk"):
                    _issue(
                        ch,
                        severity="warning",
                        code="alert_target_network",
                        message=(
                            f"alert_target #{tid_i} сеть {target.get('network')} "
                            "— доставка алертов ожидается в TG/VK"
                        ),
                    )

        errors_n = sum(1 for i in issues if i["severity"] == "error")
        warnings_n = sum(1 for i in issues if i["severity"] == "warning")
        return {
            "ok": errors_n == 0,
            "brand_id": brand_id,
            "checked": checked,
            "accessible": accessible,
            "errors": errors_n,
            "warnings": warnings_n,
            "issues": issues,
        }

    async def delete_channel(self, user_id: int, brand_id: int, channel_id: int) -> bool:
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            return False
        existing = await self.get_channel(user_id, channel_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_brand_channels WHERE id = %s AND brand_id = %s",
                    (channel_id, brand_id),
                )
                deleted = cur.rowcount > 0
        finally:
            await release_db_connection(conn)
        if deleted and existing and existing.get("network") == "url":
            await remove_curl_url_item(user_id, str(existing.get("external_id") or ""))
            await self._refresh_curl_collect_enabled(user_id)
        return deleted

    async def _refresh_curl_collect_enabled(self, user_id: int) -> None:
        """Set curl_settings.collect_enabled from any URL channel with collect_enabled."""
        from services.profile_service import profile_service

        all_ch = await self.list_all_channels(user_id)
        any_collect = any(
            c.get("network") == "url" and c.get("collect_enabled") for c in all_ch
        )
        settings = await profile_service.get_curl_settings(user_id)
        if not settings:
            return
        if bool(settings.get("collect_enabled")) == any_collect:
            return
        await profile_service.save_curl_settings(
            user_id,
            {**settings, "collect_enabled": any_collect},
        )

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
        assigned_to: Optional[int] = None,
    ) -> dict:
        media = media or []
        targets = targets or []
        from services.demo_seed_service import is_demo_external_id

        brand = await self.get_brand(user_id, brand_id) if brand_id else None
        is_demo_brand = bool(brand and brand.get("is_demo"))
        if is_demo_brand and status in ("ready", "scheduled", "publishing"):
            status = "draft"
        for t in targets:
            if is_demo_external_id(t.get("external_id")) and status in (
                "ready",
                "scheduled",
                "publishing",
            ):
                raise ValueError(
                    "Демо-канал учебного контура нельзя публиковать. "
                    "Подключите свой канал в онбординге."
                )

        tariff = await get_user_tariff(user_id)
        # Unified Posts flow: exactly one confirmed publish channel per job.
        if status in ("ready", "scheduled", "publishing", "pending_approval"):
            if len(targets) != 1:
                raise ValueError(
                    "Выберите ровно один канал с подтверждёнными правами публикации"
                )
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

        if targets and status in ("ready", "scheduled", "publishing", "pending_approval"):
            for t in targets:
                network = str(t.get("network") or "").strip()
                external_id = str(t.get("external_id") or "").strip()
                ch = await self.resolve_channel_by_external_id(
                    user_id, network, external_id
                )
                if not ch:
                    raise ValueError(
                        f"Канал {network}:{external_id} не найден в брендах"
                    )
                if brand_id is not None and ch.get("brand_id") != brand_id:
                    raise ValueError("Канал не принадлежит выбранному бренду")
                if ch.get("role") != "own":
                    raise ValueError("Публикация только в собственные каналы")
                if ch.get("auth_status") != "connected":
                    raise ValueError(
                        "Нет подтверждённых прав доступа к каналу. "
                        "Проверьте авторизацию на странице Channels."
                    )
                if ch.get("publish_enabled") is False:
                    raise ValueError("Публикация в этот канал отключена")
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
                    f"""
                    INSERT INTO smm_publish_jobs
                        (user_id, brand_id, source_text, media, targets, adapters_result,
                         publish_at, status, assigned_to)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                    RETURNING {JOB_COLUMNS}
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
                        assigned_to,
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
        status: Optional[str] = None,
        statuses: Optional[list[str]] = None,
        channel_id: Optional[int] = None,
        network: Optional[str] = None,
        assigned_to: Optional[int] = None,
        assigned_to_me: bool = False,
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
        status_list = [s for s in (statuses or []) if s]
        if status and status not in status_list:
            status_list.append(status)
        if status_list:
            conditions.append("status = ANY(%s)")
            params.append(status_list)
        if assigned_to_me:
            conditions.append("assigned_to = %s")
            params.append(user_id)
        elif assigned_to is not None:
            conditions.append("assigned_to = %s")
            params.append(assigned_to)
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {JOB_COLUMNS}
                    FROM smm_publish_jobs
                    WHERE {where}
                    ORDER BY COALESCE(publish_at, created_at) DESC
                    LIMIT 500
                    """,
                    params,
                )
                rows = await cur.fetchall()
                jobs = [_row_job(r) for r in rows]
        finally:
            await release_db_connection(conn)

        if channel_id is not None or network:
            channel_keys: set[tuple[str, str]] = set()
            if channel_id is not None:
                channels = await self.list_all_channels(user_id)
                ch = next((c for c in channels if c["id"] == channel_id), None)
                if not ch:
                    return []
                channel_keys.add((normalize_network(ch["network"]), str(ch["external_id"])))
            net_filter = normalize_network(network) if network else None

            def _matches(job: dict) -> bool:
                targets = job.get("targets") or []
                if not targets:
                    return False
                for t in targets:
                    t_net = normalize_network(t.get("network"))
                    t_ext = str(t.get("external_id") or "")
                    if channel_keys and (t_net, t_ext) not in channel_keys:
                        continue
                    if net_filter and t_net != net_filter:
                        continue
                    return True
                return False

            jobs = [j for j in jobs if _matches(j)]
        return jobs

    async def update_job(self, user_id: int, job_id: int, **fields: Any) -> Optional[dict]:
        allowed = {
            "source_text",
            "media",
            "targets",
            "publish_at",
            "status",
            "adapters_result",
            "assigned_to",
            "rejection_comment",
        }
        if "publish_at" in fields and fields["publish_at"]:
            tariff = await get_user_tariff(user_id)
            if not plan_feature(tariff, "schedule", True):
                raise QuotaExceededError(resource="feature:schedule", limit=0, used=0)
            pub_raw = fields["publish_at"]
            try:
                pub_at = (
                    datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
                    if isinstance(pub_raw, str)
                    else pub_raw
                )
            except ValueError:
                pub_at = None
            if pub_at:
                horizon = plan_limit(tariff, "schedule_horizon_days", 7)
                now = datetime.utcnow()
                pub_naive = pub_at.replace(tzinfo=None) if getattr(pub_at, "tzinfo", None) else pub_at
                if pub_naive > now + timedelta(days=horizon):
                    raise QuotaExceededError(
                        resource="schedule_horizon_days", limit=horizon, used=horizon + 1
                    )
        updates = []
        params: list[Any] = []
        for key, val in fields.items():
            if key not in allowed:
                continue
            if key in ("media", "targets", "adapters_result"):
                if val is None:
                    continue
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
            elif key in ("assigned_to", "rejection_comment"):
                updates.append(f"{key} = %s")
                params.append(val)
            elif val is None:
                continue
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
                    RETURNING {JOB_COLUMNS}
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
        tariff = await get_user_tariff(user_id)
        use_approval = plan_feature(tariff, "approval_workflow")
        default_status = "pending_approval" if use_approval else "draft"
        if use_approval:
            await ensure_smm_feature(user_id, "approval_workflow")
        for i, row in enumerate(reader, start=2):
            text = (row.get("text") or row.get("post_text") or row.get("content") or "").strip()
            if not text:
                errors.append({"line": i, "error": "empty text"})
                continue
            publish_at = (row.get("publish_at") or row.get("scheduled_at") or "").strip() or None
            network = (row.get("network") or "").strip().lower()
            external_id = (row.get("channel") or row.get("external_id") or "").strip()
            assigned_raw = (row.get("assigned_to") or "").strip()
            assigned_to = int(assigned_raw) if assigned_raw.isdigit() else None
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
                    status=default_status,
                    assigned_to=assigned_to,
                )
                created.append(job["id"])
            except Exception as exc:
                errors.append({"line": i, "error": str(exc)})
        return {
            "created": len(created),
            "job_ids": created,
            "errors": errors,
            "status": default_status,
        }

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
        cfg = dict(config or {})
        if "require_approval" not in cfg:
            tariff = await get_user_tariff(user_id)
            cfg["require_approval"] = bool(plan_feature(tariff, "approval_workflow"))
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO smm_automations (user_id, brand_id, type, config, enabled)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    RETURNING id, user_id, brand_id, type, config, enabled, created_at, updated_at
                    """,
                    (user_id, brand_id, type_, json.dumps(cfg), enabled),
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
        inserted = 0
        alerts = 0
        skipped_interval = 0
        new_rows: list[dict[str, Any]] = []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if user_id is not None:
                    await cur.execute(
                        """
                        SELECT c.id, c.network, c.external_id, b.user_id, c.role,
                               c.brand_id, c.title, c.alert_enabled, c.alert_delivery,
                               c.processing
                        FROM smm_brand_channels c
                        JOIN smm_brands b ON b.id = c.brand_id
                        WHERE b.user_id = %s AND c.role IN ('competitor', 'source')
                        """,
                        (user_id,),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT c.id, c.network, c.external_id, b.user_id, c.role,
                               c.brand_id, c.title, c.alert_enabled, c.alert_delivery,
                               c.processing
                        FROM smm_brand_channels c
                        JOIN smm_brands b ON b.id = c.brand_id
                        WHERE c.role IN ('competitor', 'source')
                        """
                    )
                channels = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        for row in channels:
            (
                ch_id,
                network,
                external_id,
                uid,
                role,
                brand_id,
                title,
                alert_enabled,
                alert_delivery,
                processing,
            ) = row
            interval_min = _competitor_sync_interval(processing)
            last_collected = await self._competitor_last_collected(ch_id)
            if last_collected:
                last_naive = (
                    last_collected.replace(tzinfo=None)
                    if getattr(last_collected, "tzinfo", None)
                    else last_collected
                )
                if datetime.utcnow() - last_naive < timedelta(minutes=interval_min):
                    skipped_interval += 1
                    continue

            posts = await self._fetch_competitor_source_posts(
                uid, str(network), str(external_id)
            )
            for post in posts:
                snap = await self._insert_competitor_snapshot(ch_id, post)
                if not snap:
                    continue
                inserted += 1
                delivery = alert_delivery
                if isinstance(delivery, str):
                    try:
                        delivery = json.loads(delivery)
                    except (json.JSONDecodeError, TypeError):
                        delivery = {}
                if not isinstance(delivery, dict):
                    delivery = {}
                if role == "competitor":
                    new_rows.append(
                        {
                            "channel_id": ch_id,
                            "brand_id": brand_id,
                            "user_id": uid,
                            "network": network,
                            "title": title,
                            "alert_enabled": bool(alert_enabled),
                            "alert_delivery": delivery,
                            "snapshot": snap,
                        }
                    )

        for item in new_rows:
            if not item.get("alert_enabled"):
                continue
            try:
                ok = await self._alert_competitor_new_post(item)
                if ok:
                    alerts += 1
            except Exception as exc:
                logger.warning(
                    "Competitor alert failed channel=%s: %s",
                    item.get("channel_id"),
                    exc,
                )

        return {
            "inserted": inserted,
            "channels": len(channels),
            "alerts": alerts,
            "skipped_interval": skipped_interval,
        }

    async def _competitor_last_collected(self, channel_id: int) -> Optional[datetime]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT MAX(collected_at) FROM smm_competitor_snapshots
                    WHERE channel_id = %s
                    """,
                    (channel_id,),
                )
                row = await cur.fetchone()
                return row[0] if row and row[0] else None
        finally:
            await release_db_connection(conn)

    async def _fetch_competitor_source_posts(
        self, user_id: int, network: str, external_id: str
    ) -> list[dict[str, Any]]:
        """Normalize recent posts from tg/vk/url tables into snapshot-ready dicts."""
        ext = str(external_id or "").strip()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if network == "vk":
                    variants = _external_id_variants(ext)
                    if not variants:
                        return []
                    placeholders = ", ".join(["%s"] * len(variants))
                    await cur.execute(
                        f"""
                        SELECT vk_source_id::text, post_text, views, likes, comments, reposts,
                               post_date, NULL::text AS post_url
                        FROM vk_posts
                        WHERE user_id = %s AND domain IN ({placeholders})
                        ORDER BY post_date DESC NULLS LAST
                        LIMIT 20
                        """,
                        (user_id, *variants),
                    )
                elif network == "url":
                    page_url = ""
                    item = await get_curl_url_item(user_id, ext)
                    if item:
                        page_url = str(item.get("url") or "").strip()
                    if page_url:
                        await cur.execute(
                            """
                            SELECT id::text, post_text, views, likes, comments, reposts,
                                   COALESCE(post_date, created_at), url
                            FROM url_posts
                            WHERE user_id = %s
                              AND (
                                    url = %s
                                 OR url = %s
                                 OR url LIKE %s
                              )
                            ORDER BY COALESCE(post_date, created_at) DESC NULLS LAST
                            LIMIT 20
                            """,
                            (
                                user_id,
                                page_url,
                                page_url.rstrip("/"),
                                page_url.rstrip("/") + "%",
                            ),
                        )
                    else:
                        return []
                elif network == "tg":
                    await cur.execute(
                        """
                        SELECT id::text, post_text, views, likes, comments, reposts,
                               post_date, NULL::text AS post_url
                        FROM tg_posts
                        WHERE user_id = %s AND domain = %s
                        ORDER BY post_date DESC NULLS LAST
                        LIMIT 20
                        """,
                        (user_id, ext),
                    )
                else:
                    # Unsupported competitor network in v1
                    return []

                rows = await cur.fetchall()
                out: list[dict[str, Any]] = []
                for r in rows:
                    text = (r[1] or "") if r[1] is not None else ""
                    post_url = r[7] if len(r) > 7 else None
                    out.append(
                        {
                            "external_post_id": str(r[0]),
                            "post_text": text,
                            "views": int(r[2] or 0),
                            "likes": int(r[3] or 0),
                            "comments": int(r[4] or 0),
                            "reposts": int(r[5] or 0),
                            "posted_at": r[6],
                            "post_url": post_url,
                            "text_hash": _text_hash(text),
                        }
                    )
                return out
        finally:
            await release_db_connection(conn)

    async def _insert_competitor_snapshot(
        self, channel_id: int, post: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Insert snapshot if new by external_post_id or text_hash. Returns row or None."""
        ext_post_id = str(post.get("external_post_id") or "").strip() or None
        text = post.get("post_text") or ""
        text_hash = post.get("text_hash") or _text_hash(text)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if ext_post_id:
                    await cur.execute(
                        """
                        SELECT id FROM smm_competitor_snapshots
                        WHERE channel_id = %s AND external_post_id = %s
                        LIMIT 1
                        """,
                        (channel_id, ext_post_id),
                    )
                    if await cur.fetchone():
                        return None
                if text_hash:
                    await cur.execute(
                        """
                        SELECT id FROM smm_competitor_snapshots
                        WHERE channel_id = %s AND text_hash = %s
                        LIMIT 1
                        """,
                        (channel_id, text_hash),
                    )
                    if await cur.fetchone():
                        return None
                try:
                    await cur.execute(
                        """
                        INSERT INTO smm_competitor_snapshots
                            (channel_id, external_post_id, post_text, post_url, text_hash,
                             views, likes, comments, reposts, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, external_post_id, post_text, post_url, text_hash,
                                  views, likes, comments, reposts, posted_at, collected_at
                        """,
                        (
                            channel_id,
                            ext_post_id,
                            text,
                            post.get("post_url"),
                            text_hash,
                            post.get("views", 0),
                            post.get("likes", 0),
                            post.get("comments", 0),
                            post.get("reposts", 0),
                            post.get("posted_at"),
                        ),
                    )
                except Exception as exc:
                    msg = str(exc).lower()
                    if "post_url" in msg or "text_hash" in msg or "column" in msg:
                        # Patch not applied yet — fall back to legacy columns
                        await cur.execute(
                            """
                            INSERT INTO smm_competitor_snapshots
                                (channel_id, external_post_id, post_text,
                                 views, likes, comments, reposts, posted_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id, external_post_id, post_text, NULL::text, NULL::text,
                                      views, likes, comments, reposts, posted_at, collected_at
                            """,
                            (
                                channel_id,
                                ext_post_id,
                                text,
                                post.get("views", 0),
                                post.get("likes", 0),
                                post.get("comments", 0),
                                post.get("reposts", 0),
                                post.get("posted_at"),
                            ),
                        )
                    elif "unique" in msg or "duplicate" in msg:
                        return None
                    else:
                        raise
                row = await cur.fetchone()
                if not row:
                    return None
                return {
                    "id": row[0],
                    "external_post_id": row[1],
                    "text": row[2],
                    "url": row[3],
                    "text_hash": row[4],
                    "views": row[5],
                    "likes": row[6],
                    "comments": row[7],
                    "reposts": row[8],
                    "posted_at": row[9].isoformat() if row[9] else None,
                    "collected_at": row[10].isoformat() if row[10] else None,
                }
        finally:
            await release_db_connection(conn)

    async def _alert_competitor_new_post(self, item: dict[str, Any]) -> bool:
        """Create inbox alert for a new competitor post (dedup via external_msg_id)."""
        snap = item.get("snapshot") or {}
        network = str(item.get("network") or "tg")
        if network not in (
            "tg",
            "vk",
            "url",
            "instagram",
            "threads",
            "tw",
            "dzen",
            "wp",
        ):
            network = "tg"
        ext_id = snap.get("external_post_id") or snap.get("id")
        external_msg_id = f"comp:{item['channel_id']}:{ext_id}"
        delivery = item.get("alert_delivery") or {}
        if not isinstance(delivery, dict):
            delivery = {}
        preview = (snap.get("text") or "").strip()
        if len(preview) > 400:
            preview = preview[:397] + "..."
        title = item.get("title") or f"channel {item['channel_id']}"
        text = f"Конкурент «{title}» опубликовал новый пост"
        if preview:
            text = f"{text}:\n{preview}"
        meta = {
            "kind": "competitor_new_post",
            "snapshot_id": snap.get("id"),
            "text_hash": snap.get("text_hash"),
            "post_url": snap.get("url"),
            "posted_at": snap.get("posted_at"),
            "tg_channel_to_post": delivery.get("channel_to_post"),
            "alert_targets": delivery.get("alert_targets") or [],
            "alert_text": delivery.get("alert_text"),
        }
        result = await self.ingest_inbox_item(
            int(item["user_id"]),
            {
                "brand_id": item.get("brand_id"),
                "network": network,
                "channel_id": item.get("channel_id"),
                "type": "competitor_post",
                "author": title,
                "text": text,
                "external_msg_id": external_msg_id,
                "status": "new",
                "meta": meta,
            },
        )
        if result.get("deduped"):
            return False
        if item.get("channel_id"):
            await self.bump_channel_counter(
                int(item["user_id"]), int(item["channel_id"]), alerts_sent=1
            )
        return True

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

    async def competitor_posts(
        self,
        user_id: int,
        channel_id: int,
        *,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[dict]:
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
                params: list[Any] = [channel_id]
                since_sql = ""
                if since is not None:
                    since_sql = "AND COALESCE(posted_at, collected_at) >= %s"
                    params.append(since)
                params.append(limit)
                try:
                    await cur.execute(
                        f"""
                        SELECT id, external_post_id, post_text, views, likes, comments, reposts,
                               posted_at, collected_at, post_url, text_hash
                        FROM smm_competitor_snapshots
                        WHERE channel_id = %s {since_sql}
                        ORDER BY COALESCE(posted_at, collected_at) DESC
                        LIMIT %s
                        """,
                        tuple(params),
                    )
                except Exception:
                    await cur.execute(
                        f"""
                        SELECT id, external_post_id, post_text, views, likes, comments, reposts,
                               posted_at, collected_at, NULL::text, NULL::text
                        FROM smm_competitor_snapshots
                        WHERE channel_id = %s {since_sql}
                        ORDER BY COALESCE(posted_at, collected_at) DESC
                        LIMIT %s
                        """,
                        tuple(params),
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
                        "url": r[9],
                        "text_hash": r[10],
                    }
                    for r in rows
                ]
        finally:
            await release_db_connection(conn)

    async def competitor_digest(
        self,
        user_id: int,
        channel_id: int,
        period: str = "24h",
        *,
        with_ai: bool = True,
    ) -> dict:
        await ensure_smm_feature(user_id, "competitors")
        since = _period_since(period)
        posts = await self.competitor_posts(user_id, channel_id, since=since, limit=100)
        summary = None
        fallback = False
        if with_ai and posts:
            blob = "\n\n".join(
                (p.get("text") or "").strip() for p in posts if (p.get("text") or "").strip()
            )[:6000]
            if blob:
                try:
                    from services.quota_service import ensure_ai_calls_quota
                    from shared.ai_client import summarize

                    await ensure_ai_calls_quota(user_id)
                    summary = await summarize(blob, 800)
                except QuotaExceededError:
                    raise
                except Exception as exc:
                    logger.warning("Competitor digest AI fallback: %s", exc)
                    summary = blob[:800] + ("..." if len(blob) > 800 else "")
                    fallback = True
        return {
            "channel_id": channel_id,
            "period": period,
            "since": since.isoformat() + "Z",
            "posts_count": len(posts),
            "posts": posts,
            "summary": summary,
            "fallback": fallback,
        }

    async def competitor_diff(
        self,
        user_id: int,
        channel_id: int,
        *,
        since: Optional[str] = None,
    ) -> dict:
        """New competitor posts since last_seen_at (ISO) or last collected watermark."""
        await ensure_smm_feature(user_id, "competitors")
        since_dt: Optional[datetime] = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
            except ValueError as exc:
                raise ValueError("Invalid since datetime") from exc
        else:
            since_dt = await self._competitor_last_collected(channel_id)
            if since_dt:
                # Exclude the latest batch watermark: return only strictly newer
                since_dt = since_dt.replace(tzinfo=None) - timedelta(seconds=1)
        posts = await self.competitor_posts(
            user_id, channel_id, since=since_dt, limit=100
        )
        last_seen = None
        if posts:
            last_seen = posts[0].get("collected_at") or posts[0].get("posted_at")
        return {
            "channel_id": channel_id,
            "since": since_dt.isoformat() + "Z" if since_dt else None,
            "last_seen_at": last_seen,
            "new_posts": posts,
            "count": len(posts),
        }

    async def competitor_compare(
        self,
        user_id: int,
        brand_id: int,
        competitor_channel_id: int,
        period: str = "7d",
    ) -> dict:
        """Compare own brand posting vs a competitor channel."""
        await ensure_smm_feature(user_id, "competitors")
        brand = await self.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        since = _period_since(period)
        comp_posts = await self.competitor_posts(
            user_id, competitor_channel_id, since=since, limit=200
        )
        if not comp_posts and not await self.get_channel(user_id, competitor_channel_id):
            raise ValueError("Competitor channel not found")

        own_stats = await self._own_post_stats(user_id, brand_id, since)
        comp_stats = _posts_stats(comp_posts)
        themes = await self._competitor_top_themes(user_id, comp_posts)

        return {
            "brand_id": brand_id,
            "competitor_channel_id": competitor_channel_id,
            "period": period,
            "since": since.isoformat() + "Z",
            "own": own_stats,
            "competitor": comp_stats,
            "top_themes": themes,
        }

    async def _own_post_stats(
        self, user_id: int, brand_id: int, since: datetime
    ) -> dict[str, Any]:
        channels = await self.list_channels(user_id, brand_id)
        own = [c for c in channels if c.get("role") == "own"]
        texts: list[str] = []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                for ch in own:
                    net = ch.get("network")
                    ext = str(ch.get("external_id") or "").strip()
                    if not ext:
                        continue
                    if net == "vk":
                        await cur.execute(
                            """
                            SELECT post_text FROM vk_posts
                            WHERE user_id = %s AND domain = %s
                              AND COALESCE(post_date, created_at) >= %s
                            ORDER BY post_date DESC NULLS LAST
                            LIMIT 100
                            """,
                            (user_id, ext.lstrip("-"), since),
                        )
                    elif net == "tg":
                        await cur.execute(
                            """
                            SELECT post_text FROM tg_posts
                            WHERE user_id = %s AND domain = %s
                              AND COALESCE(post_date, created_at) >= %s
                            ORDER BY post_date DESC NULLS LAST
                            LIMIT 100
                            """,
                            (user_id, ext, since),
                        )
                    else:
                        continue
                    for r in await cur.fetchall():
                        if r[0]:
                            texts.append(str(r[0]))
        finally:
            await release_db_connection(conn)
        return _texts_stats(texts)

    async def _competitor_top_themes(
        self, user_id: int, posts: list[dict]
    ) -> list[dict[str, Any]]:
        if not posts:
            return []
        counts: dict[str, int] = {}
        sample = posts[:12]
        try:
            from services.quota_service import ensure_ai_calls_quota
            from shared.ai_client import classify

            await ensure_ai_calls_quota(user_id)
            for p in sample:
                text = (p.get("text") or "").strip()
                if not text:
                    continue
                try:
                    result = await classify(text, COMPETITOR_DEFAULT_THEMES)
                    cat = str(result.get("category") or "другое")
                    counts[cat] = counts.get(cat, 0) + 1
                except Exception:
                    counts["другое"] = counts.get("другое", 0) + 1
        except QuotaExceededError:
            # Frequency-only compare without themes when quota exhausted
            return []
        except Exception as exc:
            logger.warning("Competitor theme classify failed: %s", exc)
            return []
        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"theme": k, "count": v} for k, v in ranked]

    async def add_competitor_snapshot(
        self, channel_id: int, data: dict
    ) -> dict:
        snap = await self._insert_competitor_snapshot(
            channel_id,
            {
                "external_post_id": data.get("external_post_id"),
                "post_text": data.get("post_text"),
                "post_url": data.get("post_url") or data.get("url"),
                "views": data.get("views", 0),
                "likes": data.get("likes", 0),
                "comments": data.get("comments", 0),
                "reposts": data.get("reposts", 0),
                "posted_at": data.get("posted_at"),
                "text_hash": data.get("text_hash"),
            },
        )
        if not snap:
            return {"id": None, "deduped": True}
        return {"id": snap["id"]}

    async def list_competitors(
        self, user_id: int, brand_id: Optional[int] = None
    ) -> list[dict]:
        channels = (
            await self.list_channels(user_id, brand_id)
            if brand_id
            else await self.list_all_channels(user_id)
        )
        return [c for c in channels if c.get("role") == "competitor"]

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

    async def get_channel_connect_status(self, user_id: int, channel_id: int) -> dict[str, Any]:
        """connected / last collect / last publish for channel workspace."""
        from services.platform_auth_service import platform_auth_service

        ch = await self.get_channel(user_id, channel_id)
        if not ch:
            raise ValueError("Channel not found")

        network = normalize_network(ch.get("network"))
        platforms = await platform_auth_service.get_all_platform_status(user_id)
        platform = platforms.get(network) or {}

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COALESCE(SUM(sent), 0), COALESCE(SUM(received), 0),
                           MAX(day)
                    FROM smm_channel_counters
                    WHERE user_id = %s AND channel_id = %s
                    """,
                    (user_id, channel_id),
                )
                row = await cur.fetchone()
                sent_total = int(row[0] or 0) if row else 0
                received_total = int(row[1] or 0) if row else 0

                await cur.execute(
                    """
                    SELECT MAX(day) FROM smm_channel_counters
                    WHERE user_id = %s AND channel_id = %s AND sent > 0
                    """,
                    (user_id, channel_id),
                )
                last_pub = await cur.fetchone()
                await cur.execute(
                    """
                    SELECT MAX(day) FROM smm_channel_counters
                    WHERE user_id = %s AND channel_id = %s AND received > 0
                    """,
                    (user_id, channel_id),
                )
                last_col = await cur.fetchone()
        finally:
            await release_db_connection(conn)

        connected = (
            ch.get("auth_status") == "connected"
            or ch.get("auth_status") == "not_required"
            or bool(platform.get("connected"))
        )
        return {
            "channel_id": channel_id,
            "network": network,
            "network_label": network_label(network),
            "external_id": ch.get("external_id"),
            "title": ch.get("title"),
            "role": ch.get("role"),
            "connected": connected,
            "auth_status": ch.get("auth_status"),
            "auth_error": ch.get("auth_error"),
            "auth_checked_at": ch.get("auth_checked_at"),
            "auth_capabilities": ch.get("auth_capabilities") or {},
            "platform_connected": bool(platform.get("connected")),
            "setup_url": setup_url(network),
            "publish_enabled": ch.get("publish_enabled"),
            "collect_enabled": ch.get("collect_enabled"),
            "alert_enabled": ch.get("alert_enabled"),
            "last_publish_day": str(last_pub[0]) if last_pub and last_pub[0] else None,
            "last_collect_day": str(last_col[0]) if last_col and last_col[0] else None,
            "sent_total": sent_total,
            "received_total": received_total,
        }

    async def bind_channel_profile(
        self,
        user_id: int,
        channel_id: int,
        *,
        external_id: Optional[str] = None,
        title: Optional[str] = None,
        from_profile: bool = False,
    ) -> dict[str, Any]:
        """Set external_id from explicit value or from connected *_profiles handle."""
        from services.platform_auth_service import platform_auth_service

        ch = await self.get_channel(user_id, channel_id)
        if not ch:
            raise ValueError("Channel not found")
        network = normalize_network(ch.get("network"))
        if network == "url":
            raise ValueError("URL channels are bound via url_config, not profile")

        ext = (external_id or "").strip()
        if from_profile or not ext:
            suggested = await platform_auth_service.suggest_profile_external_id(
                user_id, network
            )
            if not suggested:
                raise ValueError(
                    f"Нет handle в профиле {network_label(network)}. "
                    f"Подключите аккаунт: {setup_url(network)}"
                )
            ext = suggested

        fields: dict[str, Any] = {"external_id": ext}
        if title is not None:
            fields["title"] = title
        elif not ch.get("title"):
            fields["title"] = ext

        updated = await self.update_channel(
            user_id, ch["brand_id"], channel_id, **fields
        )
        if not updated:
            raise ValueError("Channel not found")

        probe = await platform_auth_service.recheck_channel_auth(user_id, channel_id)
        refreshed = await self.get_channel(user_id, channel_id)
        return {**(refreshed or updated), "bind": {"external_id": ext}, "auth": probe}

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
        network = normalize_network(network)
        channels = await self.list_all_channels(user_id)
        for c in channels:
            if normalize_network(c.get("network")) != network:
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
                    f"""
                    SELECT {JOB_COLUMNS}
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
        from services.demo_seed_service import is_demo_external_id

        job_id = job["id"]
        user_id = job["user_id"]
        targets = job.get("targets") or []
        media = job.get("media") or []
        text = job.get("source_text") or ""
        adapters = job.get("adapters_result") or {}
        per_target: dict[str, Any] = (
            dict(adapters["targets"]) if isinstance(adapters.get("targets"), dict) else {}
        )

        brand = None
        if job.get("brand_id"):
            brand = await self.get_brand(user_id, int(job["brand_id"]))
        if brand and brand.get("is_demo"):
            await self.update_job(
                user_id,
                job_id,
                status="failed",
                adapters_result={
                    **adapters,
                    "error": "Demo brand publish blocked (учебный контур S01)",
                },
            )
            return {
                "id": job_id,
                "status": "failed",
                "error": "Demo brand publish blocked",
            }

        channels = await self.list_all_channels(user_id)
        from services.platform_auth_service import PlatformAction, PlatformAuthError, platform_auth_service

        await self.update_job(user_id, job_id, status="publishing")
        ok = 0
        fail = 0
        for t in targets:
            network = normalize_network(t.get("network"))
            external_id = str(t.get("external_id") or "")
            key = f"{network}:{external_id}"
            if is_demo_external_id(external_id):
                per_target[key] = {
                    "status": "failed",
                    "error": "demo channel publish blocked",
                }
                fail += 1
                continue
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
                    if normalize_network(c["network"]) == network
                    and str(c["external_id"]) == external_id
                ),
                None,
            )
            if not ch:
                per_target[key] = {"status": "failed", "error": "channel_not_found"}
                fail += 1
                continue
            if ch.get("role") != "own" or ch.get("auth_status") != "connected":
                per_target[key] = {
                    "status": "failed",
                    "error": "channel_not_connected",
                }
                fail += 1
                continue
            if ch.get("publish_enabled") is False:
                per_target[key] = {"status": "skipped", "error": "publish_enabled=false"}
                fail += 1
                continue
            try:
                plain_default = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()
                if network == "tg":
                    await ensure_monthly_post_quota(user_id, units=1)
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
                    await ensure_monthly_post_quota(user_id, units=1)
                    vk_payload = adapters.get("vk") or {}
                    vk_text = vk_payload.get("text", plain_default)
                    await post_service.create_vk_post_record(
                        user_id=user_id,
                        text=vk_text,
                        images=media,
                        to_vk=True,
                        target_groups=[external_id] if external_id else None,
                        skip_quota=True,
                    )
                elif network == "tw":
                    tw_text = (adapters.get("tw") or {}).get("text", plain_default)[:280]
                    await post_service.create_tw_post_record(
                        user_id=user_id,
                        text=tw_text,
                        to_tw=True,
                        target_channels=[external_id] if external_id else None,
                    )
                elif network == "wp":
                    wp_text = (adapters.get("wp") or {}).get("text", text)
                    await post_service.create_wp_post_record(
                        user_id=user_id,
                        text=wp_text,
                        to_wp=True,
                        target_channels=[external_id] if external_id else None,
                    )
                elif network == "threads":
                    th_text = (adapters.get("threads") or {}).get("text", plain_default)[:500]
                    await post_service.create_threads_post_record(
                        user_id=user_id,
                        text=th_text,
                        images=media if media else None,
                        to_threads=True,
                        target_channels=[external_id] if external_id else None,
                    )
                elif network == "dzen":
                    dz_text = (adapters.get("dzen") or {}).get("text", plain_default)
                    await post_service.create_dzen_post_record(
                        user_id=user_id,
                        text=dz_text,
                        images=media if media else None,
                        to_dzen=True,
                        target_channels=[external_id] if external_id else None,
                    )
                elif network == "instagram":
                    ig_text = (adapters.get("instagram") or {}).get("text", plain_default)
                    await post_service.create_instagram_post_record(
                        user_id=user_id,
                        caption=ig_text,
                        images=media if media else None,
                        to_instagram=True,
                        target_channels=[external_id] if external_id else None,
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
        if item_type not in ("dm", "comment", "reaction", "competitor_post"):
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
        job = await self.get_job(user_id, job_id)
        if not job:
            return None
        if job.get("status") not in ("pending_approval", "draft", "rejected"):
            raise ValueError(f"Cannot approve job in status {job.get('status')}")
        from services.demo_seed_service import is_demo_external_id

        if job.get("brand_id"):
            brand = await self.get_brand(user_id, int(job["brand_id"]))
            if brand and brand.get("is_demo"):
                raise ValueError(
                    "Учебный демо-бренд нельзя выводить в публикацию. "
                    "Подключите свой канал в онбординге."
                )
        for t in job.get("targets") or []:
            if is_demo_external_id(t.get("external_id")):
                raise ValueError(
                    "Демо-канал учебного контура нельзя публиковать."
                )
        next_status = "scheduled" if job.get("publish_at") else "ready"
        return await self.update_job(
            user_id,
            job_id,
            status=next_status,
            rejection_comment=None,
        )

    async def reject_job(
        self, user_id: int, job_id: int, comment: Optional[str] = None
    ) -> Optional[dict]:
        await ensure_smm_feature(user_id, "approval_workflow")
        job = await self.get_job(user_id, job_id)
        if not job:
            return None
        if job.get("status") not in ("pending_approval", "draft"):
            raise ValueError(f"Cannot reject job in status {job.get('status')}")
        return await self.update_job(
            user_id,
            job_id,
            status="rejected",
            rejection_comment=(comment or "").strip() or None,
        )

    async def assign_job(
        self, user_id: int, job_id: int, assigned_to: Optional[int]
    ) -> Optional[dict]:
        await ensure_smm_feature(user_id, "approval_workflow")
        return await self.update_job(user_id, job_id, assigned_to=assigned_to)

    async def bulk_approve_jobs(self, user_id: int, job_ids: list[int]) -> dict:
        await ensure_smm_feature(user_id, "approval_workflow")
        approved: list[int] = []
        errors: list[dict] = []
        for jid in job_ids:
            try:
                job = await self.approve_job(user_id, jid)
                if job:
                    approved.append(jid)
                else:
                    errors.append({"job_id": jid, "error": "not found"})
            except Exception as exc:
                errors.append({"job_id": jid, "error": str(exc)})
        return {"approved": len(approved), "job_ids": approved, "errors": errors}

    async def bulk_reschedule_jobs(
        self, user_id: int, job_ids: list[int], publish_at: str
    ) -> dict:
        updated: list[int] = []
        errors: list[dict] = []
        for jid in job_ids:
            try:
                job = await self.update_job(
                    user_id, jid, publish_at=publish_at, status="scheduled"
                )
                if job:
                    updated.append(jid)
                else:
                    errors.append({"job_id": jid, "error": "not found"})
            except Exception as exc:
                errors.append({"job_id": jid, "error": str(exc)})
        return {"updated": len(updated), "job_ids": updated, "errors": errors}

    async def get_job(self, user_id: int, job_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {JOB_COLUMNS}
                    FROM smm_publish_jobs
                    WHERE id = %s AND user_id = %s
                    """,
                    (job_id, user_id),
                )
                row = await cur.fetchone()
                return _row_job(row) if row else None
        finally:
            await release_db_connection(conn)

    async def run_automation(
        self, user_id: int, automation_id: int, limit: int = 10
    ) -> dict:
        """Fetch RSS (or enqueue placeholder for other types) → publish jobs in review queue."""
        autos = await self.list_automations(user_id)
        auto = next((a for a in autos if a["id"] == automation_id), None)
        if not auto:
            raise ValueError("Automation not found")
        if not auto.get("enabled"):
            raise ValueError("Automation is disabled")
        if auto.get("type") != "rss":
            raise ValueError("Only RSS automations support run-once for now")

        config = dict(auto.get("config") or {})
        source_url = (config.get("source_url") or "").strip()
        if not source_url:
            raise ValueError("RSS source_url is required")

        tariff = await get_user_tariff(user_id)
        require_approval = config.get("require_approval")
        if require_approval is None:
            require_approval = plan_feature(tariff, "approval_workflow")
        if require_approval:
            await ensure_smm_feature(user_id, "approval_workflow")
        status = "pending_approval" if require_approval else "draft"

        target_ids = config.get("target_channel_ids") or []
        channels = await self.list_all_channels(user_id)
        targets = [
            {"network": c["network"], "external_id": c["external_id"]}
            for c in channels
            if c["id"] in target_ids and c.get("role") == "own"
        ]
        suffix = (config.get("suffix") or "").strip()
        seen = list(config.get("seen_ids") or [])
        seen_set = set(str(x) for x in seen)

        items = await self._fetch_rss_items(source_url, limit=max(limit * 3, 20))
        created: list[int] = []
        skipped = 0
        for item in items:
            if len(created) >= limit:
                break
            item_id = str(item.get("id") or item.get("link") or item.get("title") or "")
            if not item_id or item_id in seen_set:
                skipped += 1
                continue
            text = (item.get("title") or "").strip()
            body = (item.get("summary") or "").strip()
            if body and body not in text:
                text = f"{text}\n\n{body}" if text else body
            if suffix:
                text = f"{text}\n\n{suffix}".strip()
            if not text:
                skipped += 1
                continue
            job = await self.create_job(
                user_id=user_id,
                brand_id=auto.get("brand_id"),
                text=text,
                media=[],
                targets=targets,
                adapt=True,
                status=status,
            )
            created.append(job["id"])
            seen_set.add(item_id)
            seen.append(item_id)

        config["seen_ids"] = seen[-200:]
        await self.update_automation(user_id, automation_id, config=config)
        return {
            "created": len(created),
            "job_ids": created,
            "skipped": skipped,
            "status": status,
        }

    async def _fetch_rss_items(self, url: str, limit: int = 20) -> list[dict]:
        import httpx
        import xml.etree.ElementTree as ET

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            raw = resp.text

        def _local(tag: str) -> str:
            return tag.split("}")[-1].lower() if tag else ""

        root = ET.fromstring(raw)
        items: list[dict] = []
        # RSS 2.0
        for node in root.iter():
            if _local(node.tag) != "item":
                continue
            data: dict[str, str] = {}
            for child in list(node):
                name = _local(child.tag)
                if name in ("title", "link", "description", "guid", "pubdate"):
                    data[name] = (child.text or "").strip()
            items.append(
                {
                    "id": data.get("guid") or data.get("link") or data.get("title") or "",
                    "title": data.get("title") or "",
                    "link": data.get("link") or "",
                    "summary": data.get("description") or "",
                }
            )
            if len(items) >= limit:
                break
        if items:
            return items
        # Atom
        for node in root.iter():
            if _local(node.tag) != "entry":
                continue
            title = ""
            link = ""
            summary = ""
            entry_id = ""
            for child in list(node):
                name = _local(child.tag)
                if name == "title":
                    title = (child.text or "").strip()
                elif name == "id":
                    entry_id = (child.text or "").strip()
                elif name == "summary" or name == "content":
                    summary = (child.text or "").strip()
                elif name == "link":
                    href = child.attrib.get("href") or (child.text or "").strip()
                    if href:
                        link = href
            items.append(
                {
                    "id": entry_id or link or title,
                    "title": title,
                    "link": link,
                    "summary": summary,
                }
            )
            if len(items) >= limit:
                break
        return items


smm_service = SmmService()

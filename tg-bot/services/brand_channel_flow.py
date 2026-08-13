"""Load SMM brand channel flow config for TG collect/alert/processing."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


def _parse_json(value: Any, default: Any) -> Any:
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


def _row_to_channel(row: tuple, columns: List[str]) -> Dict[str, Any]:
    raw = dict(zip(columns, row))
    return {
        "id": int(raw["id"]),
        "brand_id": int(raw["brand_id"]) if raw.get("brand_id") is not None else None,
        "user_id": int(raw["user_id"]),
        "network": raw.get("network") or "tg",
        "external_id": str(raw.get("external_id") or "").strip(),
        "title": raw.get("title"),
        "collect_enabled": bool(raw.get("collect_enabled")),
        "alert_enabled": bool(raw.get("alert_enabled")),
        "publish_enabled": bool(raw.get("publish_enabled")),
        "save_conditions": _parse_json(raw.get("save_conditions"), []) or [],
        "processing": _parse_json(raw.get("processing"), {}) or {},
        "alert_delivery": _parse_json(raw.get("alert_delivery"), {}) or {},
        "alert_rules": _parse_json(raw.get("alert_rules"), []) or [],
    }


async def list_tg_flow_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """TG brand channels with collect and/or alert enabled."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            where = [
                "c.network = 'tg'",
                "(COALESCE(c.collect_enabled, FALSE) = TRUE OR COALESCE(c.alert_enabled, FALSE) = TRUE)",
            ]
            params: list[Any] = []
            if user_id is not None:
                where.append("b.user_id = %s")
                params.append(user_id)
            await cur.execute(
                f"""
                SELECT c.id, c.brand_id, b.user_id, c.network, c.external_id, c.title,
                       c.collect_enabled, c.alert_enabled, c.publish_enabled,
                       c.save_conditions, c.processing, c.alert_delivery, c.alert_rules
                FROM smm_brand_channels c
                JOIN smm_brands b ON b.id = c.brand_id
                WHERE {' AND '.join(where)}
                """,
                params,
            )
            rows = await cur.fetchall()
            if not rows:
                return []
            columns = [col.name for col in cur.description]
            return [_row_to_channel(r, columns) for r in rows]
    except Exception as exc:
        logger.debug("list_tg_flow_channels failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


async def find_channel_for_chat(
    user_id: int,
    chat_id: Any,
    channels: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Match BrandChannel by external_id ≈ event.chat_id."""
    needle = str(chat_id).strip()
    items = channels if channels is not None else await list_tg_flow_channels(user_id)
    for ch in items:
        if ch.get("user_id") != user_id:
            continue
        ext = str(ch.get("external_id") or "").strip()
        if not ext:
            continue
        if ext == needle or ext.lstrip("-") == needle.lstrip("-"):
            return ch
        try:
            if int(ext) == int(needle):
                return ch
        except (TypeError, ValueError):
            pass
    return None


def channel_alert_rules_as_profile_rules(channel: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert channel alert_rules + alert_delivery into routing_engine rule dicts."""
    delivery = channel.get("alert_delivery") or {}
    if not isinstance(delivery, dict):
        delivery = {}
    channel_to_post = (delivery.get("channel_to_post") or "").strip()
    alert_text = (delivery.get("alert_text") or "").strip()
    if not channel_to_post or not alert_text:
        return []

    external_id = str(channel.get("external_id") or "").strip()
    rules_raw = channel.get("alert_rules") or []
    if not isinstance(rules_raw, list):
        return []

    active: List[Dict[str, Any]] = []
    for rule in rules_raw:
        if not isinstance(rule, dict):
            continue
        if not rule.get("enabled", True):
            continue
        conditions = [
            c.strip()
            for c in (rule.get("save_conditions") or [])
            if isinstance(c, str) and c.strip()
        ]
        if not conditions:
            continue
        rule_id = rule.get("id") or f"ch-{channel.get('id')}"
        active.append(
            {
                "id": str(rule_id),
                "priority": int(rule.get("priority") or 0),
                "chats_to_read": [external_id] if external_id else [],
                "save_conditions": conditions,
                "conditions_mode": rule.get("conditions_mode") or "any_of",
                "category_filter": rule.get("category_filter"),
                "channel_to_post": channel_to_post,
                "channel_to_post_title": delivery.get("channel_to_post_title"),
                "alert_text": alert_text,
                "dedup_window_sec": int(rule.get("dedup_window_sec") or 3600),
                "rate_limit_per_hour": rule.get("rate_limit_per_hour"),
                "time_windows": rule.get("time_windows") or [],
                "min_text_length": int(rule.get("min_text_length") or 0),
                "include_ai_summary": bool(delivery.get("include_ai_summary")),
                "sentiment_filter": rule.get("sentiment_filter"),
                "tags": rule.get("tags") or [],
                "stop_on_match": bool(rule.get("stop_on_match")),
                "_brand_channel_id": channel.get("id"),
            }
        )
    return active

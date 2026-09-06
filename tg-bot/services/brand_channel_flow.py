"""Load SMM brand channel flow config for TG collect/alert/processing."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

_NETWORK_TO_SERVICE = {
    "tg": "telegram",
    "vk": "vkontakte",
    "wp": "wordpress",
}


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


def _parse_id_list(value: Any) -> List[int]:
    raw = _parse_json(value, [])
    if not isinstance(raw, list):
        return []
    out: List[int] = []
    for item in raw:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


def _row_to_channel(row: tuple, columns: List[str]) -> Dict[str, Any]:
    raw = dict(zip(columns, row))
    mode = (raw.get("conditions_mode") or "any_of").strip()
    if mode not in ("any_of", "all_of"):
        mode = "any_of"
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
        "conditions_mode": mode,
        "processing": _parse_json(raw.get("processing"), {}) or {},
        "publish_targets": _parse_id_list(raw.get("publish_targets")),
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
                       c.save_conditions, c.conditions_mode, c.processing, c.publish_targets,
                       c.alert_delivery, c.alert_rules
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


async def resolve_publish_targets(
    brand_id: int,
    target_ids: List[int],
) -> List[Dict[str, Any]]:
    """Resolve BrandChannel ids to external_id + network for publish."""
    ids = [int(x) for x in target_ids if x is not None]
    if not ids or not brand_id:
        return []
    placeholders = ", ".join(["%s"] * len(ids))
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, network, external_id, title, publish_enabled
                FROM smm_brand_channels
                WHERE brand_id = %s AND id IN ({placeholders}) AND role = 'own'
                """,
                (brand_id, *ids),
            )
            rows = await cur.fetchall()
            result: List[Dict[str, Any]] = []
            for row in rows:
                ext = str(row[2] or "").strip()
                if not ext:
                    continue
                result.append(
                    {
                        "id": int(row[0]),
                        "network": row[1] or "tg",
                        "external_id": ext,
                        "title": row[3],
                        "publish_enabled": bool(row[4]) if row[4] is not None else True,
                    }
                )
            return result
    except Exception as exc:
        logger.debug("resolve_publish_targets failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


def publish_targets_to_profile_fields(targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map resolved targets → target_channels + process_services for post_collector."""
    external_ids: List[str] = []
    services: List[str] = []
    for t in targets:
        ext = str(t.get("external_id") or "").strip()
        if ext:
            external_ids.append(ext)
        svc = _NETWORK_TO_SERVICE.get(str(t.get("network") or "").strip().lower())
        if svc and svc not in services:
            services.append(svc)
    return {
        "target_channels": external_ids,
        "process_services": services,
        "publish_enabled": bool(external_ids),
    }


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


def channel_alert_rules_as_profile_rules(
    channel: Dict[str, Any],
    destinations: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Convert channel alert_rules + alert_delivery into routing_engine rule dicts.

    destinations: resolved own channels [{external_id, title, network}, ...]
    from alert_delivery.alert_targets. Falls back to alert_delivery.channel_to_post.
    """
    delivery = channel.get("alert_delivery") or {}
    if not isinstance(delivery, dict):
        delivery = {}
    alert_text = (delivery.get("alert_text") or "").strip()
    if not alert_text:
        return []

    dests: List[Dict[str, Any]] = []
    for item in destinations or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("network") or "tg").lower() not in ("tg", "telegram"):
            continue
        ext = str(item.get("external_id") or "").strip()
        if not ext:
            continue
        dests.append({"external_id": ext, "title": item.get("title")})
    if not dests:
        channel_to_post = (delivery.get("channel_to_post") or "").strip()
        if channel_to_post:
            dests.append(
                {
                    "external_id": channel_to_post,
                    "title": delivery.get("channel_to_post_title"),
                }
            )
    if not dests:
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
        rule_id = str(rule.get("id") or f"ch-{channel.get('id')}")
        for dest in dests:
            dest_ext = dest["external_id"]
            active.append(
                {
                    "id": f"{rule_id}:{dest_ext}",
                    "priority": int(rule.get("priority") or 0),
                    "chats_to_read": [external_id] if external_id else [],
                    "save_conditions": conditions,
                    "conditions_mode": rule.get("conditions_mode") or "any_of",
                    "category_filter": rule.get("category_filter"),
                    "channel_to_post": dest_ext,
                    "channel_to_post_title": dest.get("title"),
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

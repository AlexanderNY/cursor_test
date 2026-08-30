"""Load SMM brand channel flow config for VK collect/alert/processing."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

_NETWORK_TO_SERVICE = {
    "tg": "telegram",
    "telegram": "telegram",
    "vk": "vkontakte",
    "vkontakte": "vkontakte",
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
    if mode not in ("any_of", "all_of", "regex"):
        mode = "any_of"
    return {
        "id": int(raw["id"]),
        "brand_id": int(raw["brand_id"]) if raw.get("brand_id") is not None else None,
        "user_id": int(raw["user_id"]),
        "network": raw.get("network") or "vk",
        "external_id": str(raw.get("external_id") or "").strip(),
        "title": raw.get("title"),
        "role": raw.get("role") or "source",
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


async def list_vk_flow_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """VK brand channels with collect and/or alert enabled."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            where = [
                "c.network = 'vk'",
                "(COALESCE(c.collect_enabled, FALSE) = TRUE OR COALESCE(c.alert_enabled, FALSE) = TRUE)",
            ]
            params: list[Any] = []
            if user_id is not None:
                where.append("b.user_id = %s")
                params.append(user_id)
            await cur.execute(
                f"""
                SELECT c.id, c.brand_id, b.user_id, c.network, c.external_id, c.title, c.role,
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
        logger.debug("list_vk_flow_channels failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


async def resolve_publish_targets(
    brand_id: int,
    target_ids: List[int],
) -> List[Dict[str, Any]]:
    """Resolve BrandChannel ids to external_id + network for publish/alert."""
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
                        "network": (row[1] or "vk").lower(),
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


def publish_targets_to_destination_fields(targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map resolved targets → to_* flags + target_channels / target_groups."""
    tg_ids: List[str] = []
    vk_ids: List[str] = []
    services: List[str] = []
    flags = {
        "to_tg": False,
        "to_tw": False,
        "to_wp": False,
        "to_vk": False,
        "to_threads": False,
        "to_dzen": False,
        "to_instagram": False,
    }
    for t in targets:
        if t.get("publish_enabled") is False:
            continue
        ext = str(t.get("external_id") or "").strip()
        if not ext:
            continue
        net = str(t.get("network") or "").strip().lower()
        svc = _NETWORK_TO_SERVICE.get(net)
        if net in ("tg", "telegram"):
            tg_ids.append(ext)
            flags["to_tg"] = True
        elif net in ("vk", "vkontakte"):
            vk_ids.append(ext)
            flags["to_vk"] = True
        if svc and svc not in services:
            services.append(svc)
    return {
        **flags,
        "target_channels": tg_ids,
        "target_groups": vk_ids,
        "process_services": services,
    }


def external_id_to_owner_id(external_id: str, *, as_user: bool = False) -> Optional[int]:
    """VK wall owner_id. Groups → negative; users → positive. Accepts club123 / -123 / 123."""
    raw = str(external_id or "").strip()
    if not raw:
        return None
    lower = raw.lower()
    if lower.startswith("club"):
        raw = lower[4:]
    elif lower.startswith("public"):
        raw = lower[6:]
    elif lower.startswith("id") and raw[2:].lstrip("-").isdigit():
        try:
            return int(raw[2:].lstrip("-") or "0") or None
        except ValueError:
            return None
    try:
        n = int(raw)
    except ValueError:
        return None
    if n == 0:
        return None
    if as_user:
        return abs(n)
    return -abs(n)


def channel_alert_rules_as_dispatch_rules(
    channel: Dict[str, Any],
    destinations: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Convert channel alert_rules into dispatchable rules (TG and/or VK dests)."""
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
        net = str(item.get("network") or "").strip().lower()
        if net not in ("tg", "telegram", "vk", "vkontakte"):
            continue
        ext = str(item.get("external_id") or "").strip()
        if not ext:
            continue
        dests.append(
            {
                "network": "tg" if net in ("tg", "telegram") else "vk",
                "external_id": ext,
                "title": item.get("title"),
            }
        )
    if not dests:
        channel_to_post = (delivery.get("channel_to_post") or "").strip()
        if channel_to_post:
            dests.append(
                {
                    "network": "tg",
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
                    "id": f"{rule_id}:{dest['network']}:{dest_ext}",
                    "priority": int(rule.get("priority") or 0),
                    "source_external_id": external_id,
                    "save_conditions": conditions,
                    "conditions_mode": rule.get("conditions_mode") or "any_of",
                    "dest_network": dest["network"],
                    "dest_external_id": dest_ext,
                    "dest_title": dest.get("title"),
                    "alert_text": alert_text,
                    "dedup_window_sec": int(rule.get("dedup_window_sec") or 3600),
                    "min_text_length": int(rule.get("min_text_length") or 0),
                    "stop_on_match": bool(rule.get("stop_on_match")),
                    "_brand_channel_id": channel.get("id"),
                }
            )
    return active

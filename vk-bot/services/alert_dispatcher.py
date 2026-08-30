"""VK collect alerts: phrase match → enqueue TG/VK ready posts (publisher delivers)."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection
from shared.text_conditions import evaluate_text_conditions

logger = logging.getLogger(__name__)

TG_MESSAGE_LIMIT = 4096
VK_MESSAGE_LIMIT = 16384


def build_alert_body(
    alert_text: str,
    source_label: str,
    message_text: str,
    *,
    limit: int = TG_MESSAGE_LIMIT,
) -> str:
    header = f"{(alert_text or '').strip()}\n\nИсточник: {source_label}\nСообщение:\n"
    body = message_text or ""
    full = header + body
    if len(full) <= limit:
        return full
    available = limit - len(header) - 3
    if available <= 0:
        return full[: limit - 3] + "..."
    return header + body[:available] + "..."


def _text_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


async def _is_deduped(
    user_id: int,
    rule_id: str,
    text_hash: str,
    window_sec: int,
) -> bool:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM vk_alert_dedup
                WHERE user_id = %s AND rule_id = %s AND text_hash = %s
                  AND created_at > CURRENT_TIMESTAMP - (%s || ' seconds')::interval
                LIMIT 1
                """,
                (user_id, rule_id, text_hash, max(60, int(window_sec or 3600))),
            )
            return bool(await cur.fetchone())
    except Exception as exc:
        # Table may not exist yet — allow send, log once-level debug
        logger.debug("vk_alert_dedup check skipped: %s", exc)
        return False
    finally:
        await release_db_connection(conn)


async def _mark_dedup(user_id: int, rule_id: str, text_hash: str) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO vk_alert_dedup (user_id, rule_id, text_hash, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, rule_id, text_hash) DO UPDATE
                SET created_at = CURRENT_TIMESTAMP
                """,
                (user_id, rule_id, text_hash),
            )
    except Exception as exc:
        logger.debug("vk_alert_dedup write skipped: %s", exc)
    finally:
        await release_db_connection(conn)


async def _enqueue_tg_alert(
    user_id: int,
    text: str,
    target_channel: str,
) -> bool:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO tg_posts (
                    user_id, post_text, status, post_type,
                    to_tg, target_channels, created_at, updated_at
                ) VALUES (
                    %s, %s, 'ready', 'tg_alert',
                    TRUE, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING id
                """,
                (user_id, text[:TG_MESSAGE_LIMIT], json.dumps([str(target_channel)])),
            )
            row = await cur.fetchone()
            return bool(row)
    except Exception as exc:
        logger.error("enqueue TG alert failed: %s", exc, exc_info=True)
        return False
    finally:
        await release_db_connection(conn)


async def _enqueue_vk_alert(
    user_id: int,
    text: str,
    target_group: str,
) -> bool:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO vk_posts (
                    user_id, post_text, status, post_type,
                    to_vk, target_groups, created_at, updated_at
                ) VALUES (
                    %s, %s, 'ready', 'vk_alert',
                    TRUE, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING id
                """,
                (user_id, text[:VK_MESSAGE_LIMIT], json.dumps([str(target_group)])),
            )
            row = await cur.fetchone()
            return bool(row)
    except Exception as exc:
        logger.error("enqueue VK alert failed: %s", exc, exc_info=True)
        return False
    finally:
        await release_db_connection(conn)


async def dispatch_alerts_for_post(
    user_id: int,
    rules: List[Dict[str, Any]],
    *,
    source_external_id: str,
    source_domain: str,
    post_text: str,
    vk_source_id: Optional[int] = None,
) -> int:
    """Match alert rules against post text; enqueue destination posts. Returns sent count."""
    if not rules:
        return 0
    text = post_text or ""
    source_label = source_external_id or source_domain
    if vk_source_id is not None:
        source_label = f"{source_label} / post {vk_source_id}"

    ordered = sorted(rules, key=lambda r: int(r.get("priority") or 0), reverse=True)
    sent = 0
    for rule in ordered:
        min_len = int(rule.get("min_text_length") or 0)
        if min_len and len(text) < min_len:
            continue
        conditions = rule.get("save_conditions") or []
        mode = rule.get("conditions_mode") or "any_of"
        matched, _ = evaluate_text_conditions(text, conditions, mode)
        if not matched:
            continue

        rule_id = str(rule.get("id") or "rule")
        th = _text_hash(f"{rule_id}:{vk_source_id}:{text}")
        if await _is_deduped(user_id, rule_id, th, int(rule.get("dedup_window_sec") or 3600)):
            continue

        dest_net = str(rule.get("dest_network") or "tg").lower()
        dest_ext = str(rule.get("dest_external_id") or "").strip()
        if not dest_ext:
            continue

        limit = TG_MESSAGE_LIMIT if dest_net == "tg" else VK_MESSAGE_LIMIT
        body = build_alert_body(
            rule.get("alert_text") or "",
            source_label,
            text,
            limit=limit,
        )

        ok = False
        if dest_net == "tg":
            ok = await _enqueue_tg_alert(user_id, body, dest_ext)
        elif dest_net == "vk":
            ok = await _enqueue_vk_alert(user_id, body, dest_ext)

        if ok:
            await _mark_dedup(user_id, rule_id, th)
            sent += 1
            logger.info(
                "VK alert queued user=%s dest=%s:%s rule=%s",
                user_id,
                dest_net,
                dest_ext,
                rule_id,
            )
            if rule.get("stop_on_match"):
                break
    return sent

"""Seed read-only demo brand for S01 season funnel."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from database import get_db_connection, release_db_connection
from services.system_settings_service import system_settings_service

DEMO_BRAND_NAME = "Учебный бренд (S01)"
DEMO_OWN_EXTERNAL_ID = "demo-own-channel"
DEMO_SOURCE_EXTERNAL_ID = "demo-source-feed"
_S01_CAMPAIGN_RE = re.compile(r"^s01", re.IGNORECASE)


def is_s01_campaign(campaign: Optional[str]) -> bool:
    if not campaign:
        return False
    return bool(_S01_CAMPAIGN_RE.match(str(campaign).strip()))


async def get_user_utm_campaign(user_id: int) -> Optional[str]:
    """Read attribution from shared users table."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT utm_campaign FROM users WHERE id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return row[0]
    finally:
        await release_db_connection(conn)


async def _load_onboarding_prefs(user_id: int) -> dict[str, Any]:
    prefs = await system_settings_service.get_value(f"smm_onboarding_{user_id}", {})
    return prefs if isinstance(prefs, dict) else {}


async def _save_onboarding_prefs(user_id: int, prefs: dict[str, Any]) -> None:
    prefs = dict(prefs)
    prefs["updated_at"] = datetime.utcnow().isoformat()
    await system_settings_service.set_value(f"smm_onboarding_{user_id}", prefs)


async def seed_demo_workspace(
    user_id: int,
    *,
    force: bool = False,
    campaign: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create demo brand + sample channels/jobs/inbox.
    Idempotent when demo_seeded already set (unless force).
    """
    prefs = await _load_onboarding_prefs(user_id)
    if prefs.get("demo_seeded") and not force:
        return {
            "seeded": True,
            "already": True,
            "brand_id": prefs.get("demo_brand_id"),
            "demo_seeded": True,
        }

    campaign = campaign if campaign is not None else await get_user_utm_campaign(user_id)
    if not force and not is_s01_campaign(campaign):
        return {
            "seeded": False,
            "already": False,
            "reason": "utm_campaign is not s01*",
            "demo_seeded": bool(prefs.get("demo_seeded")),
        }

    # Re-use existing demo brand if present
    conn = await get_db_connection()
    brand_id: Optional[int] = None
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM smm_brands
                WHERE user_id = %s AND is_demo = TRUE
                ORDER BY id ASC LIMIT 1
                """,
                (user_id,),
            )
            existing = await cur.fetchone()
            if existing:
                brand_id = int(existing[0])
            else:
                await cur.execute(
                    """
                    INSERT INTO smm_brands (
                        user_id, name, color, tone_of_voice, style_notes,
                        prompt_snippets, is_demo
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, '[]'::jsonb, TRUE
                    )
                    RETURNING id
                    """,
                    (
                        user_id,
                        DEMO_BRAND_NAME,
                        "#6366F1",
                        "Спокойный учебный тон: коротко и по делу.",
                        "Демо-контур сезона S01. Публикация отключена.",
                    ),
                )
                row = await cur.fetchone()
                brand_id = int(row[0])

            assert brand_id is not None

            async def _ensure_channel(
                network: str,
                external_id: str,
                title: str,
                role: str,
                kind: str = "channel",
            ) -> int:
                await cur.execute(
                    """
                    SELECT id FROM smm_brand_channels
                    WHERE brand_id = %s AND network = %s AND external_id = %s
                    """,
                    (brand_id, network, external_id),
                )
                found = await cur.fetchone()
                if found:
                    await cur.execute(
                        """
                        UPDATE smm_brand_channels
                        SET publish_enabled = FALSE,
                            collect_enabled = FALSE,
                            auth_status = 'not_required',
                            title = %s,
                            role = %s
                        WHERE id = %s
                        """,
                        (title, role, found[0]),
                    )
                    return int(found[0])
                await cur.execute(
                    """
                    INSERT INTO smm_brand_channels (
                        brand_id, network, external_id, title, kind, role,
                        publish_enabled, collect_enabled, alert_enabled,
                        auth_status, auth_capabilities
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        FALSE, FALSE, FALSE,
                        'not_required', '{}'::jsonb
                    )
                    RETURNING id
                    """,
                    (brand_id, network, external_id, title, kind, role),
                )
                ch = await cur.fetchone()
                return int(ch[0])

            own_ch = await _ensure_channel(
                "tg", DEMO_OWN_EXTERNAL_ID, "Demo TG (учебный)", "own"
            )
            await _ensure_channel(
                "url",
                DEMO_SOURCE_EXTERNAL_ID,
                "Demo source (read-only)",
                "source",
                kind="public",
            )

            # Sample jobs (draft / pending_approval) — never ready for publish
            await cur.execute(
                """
                SELECT COUNT(*) FROM smm_publish_jobs
                WHERE user_id = %s AND brand_id = %s
                """,
                (user_id, brand_id),
            )
            job_count = int((await cur.fetchone())[0])
            if job_count == 0:
                samples = [
                    (
                        "Черновик лабы: опишите слои UI / API / БД своим словами.",
                        "draft",
                        None,
                    ),
                    (
                        "На ревью: почему gateway не ходит в Postgres напрямую?",
                        "pending_approval",
                        (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    ),
                    (
                        "В календаре: слот под пост S01 (демо, без публикации).",
                        "pending_approval",
                        (datetime.utcnow() + timedelta(days=3)).isoformat(),
                    ),
                ]
                for text, status, pub_at in samples:
                    targets = [{"network": "tg", "external_id": DEMO_OWN_EXTERNAL_ID}]
                    await cur.execute(
                        """
                        INSERT INTO smm_publish_jobs (
                            user_id, brand_id, source_text, media, targets,
                            adapters_result, publish_at, status
                        )
                        VALUES (
                            %s, %s, %s, '[]'::jsonb, %s::jsonb,
                            '{}'::jsonb, %s, %s
                        )
                        """,
                        (
                            user_id,
                            brand_id,
                            text,
                            json.dumps(targets),
                            pub_at,
                            status,
                        ),
                    )

            await cur.execute(
                """
                SELECT COUNT(*) FROM smm_inbox_items
                WHERE user_id = %s AND brand_id = %s
                """,
                (user_id, brand_id),
            )
            inbox_count = int((await cur.fetchone())[0])
            if inbox_count == 0:
                await cur.execute(
                    """
                    INSERT INTO smm_inbox_items (
                        user_id, brand_id, network, channel_id, type,
                        author, text, status, external_msg_id, meta
                    )
                    VALUES (
                        %s, %s, 'tg', %s, 'comment',
                        'student_demo', %s, 'new', %s, %s::jsonb
                    )
                    """,
                    (
                        user_id,
                        brand_id,
                        own_ch,
                        "Демо-входящее: можно читать и архивировать. Ответы в прод не уходят.",
                        f"demo-inbox-{user_id}",
                        json.dumps({"demo": True}),
                    ),
                )
    finally:
        await release_db_connection(conn)

    prefs["demo_seeded"] = True
    prefs["demo_brand_id"] = brand_id
    prefs["demo_campaign"] = campaign
    await _save_onboarding_prefs(user_id, prefs)

    # growth event (best-effort)
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO growth_events (
                        user_id, event_type, utm_source, utm_medium, utm_campaign, meta
                    )
                    VALUES (%s, 'demo_seeded', NULL, NULL, %s, %s::jsonb)
                    """,
                    (
                        user_id,
                        campaign,
                        json.dumps({"brand_id": brand_id, "force": force}),
                    ),
                )
        finally:
            await release_db_connection(conn)
    except Exception:
        pass

    return {
        "seeded": True,
        "already": False,
        "brand_id": brand_id,
        "demo_seeded": True,
    }


def is_demo_external_id(external_id: Optional[str]) -> bool:
    ext = str(external_id or "").strip().lower()
    return ext.startswith("demo-")

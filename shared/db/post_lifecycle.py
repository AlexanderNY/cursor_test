"""Append-only post lifecycle audit helpers (not event sourcing)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

HUB_PLATFORM = "hub"


def _json_payload(payload: Optional[Mapping[str, Any]]) -> str:
    return json.dumps(dict(payload or {}), ensure_ascii=False, default=str)


async def insert_lifecycle_event(
    cur: Any,
    *,
    platform: str,
    post_id: int,
    to_status: str,
    from_status: Optional[str] = None,
    user_id: Optional[int] = None,
    job_id: Optional[int] = None,
    actor: str = "system",
    payload: Optional[Mapping[str, Any]] = None,
) -> None:
    """Best-effort insert into post_lifecycle_events. Never raises to callers."""
    try:
        await cur.execute(
            """
            INSERT INTO post_lifecycle_events
                (platform, post_id, user_id, job_id, from_status, to_status, actor, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                (platform or HUB_PLATFORM)[:20],
                int(post_id),
                user_id,
                job_id,
                from_status,
                to_status,
                (actor or "system")[:80],
                _json_payload(payload),
            ),
        )
    except Exception as exc:
        logger.debug(
            "post_lifecycle_event skipped platform=%s post_id=%s: %s",
            platform,
            post_id,
            exc,
        )


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def build_post_trace_timeline(
    *,
    hub: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    lifecycle_events: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Merge stored lifecycle rows with synthetic stages from current hub/targets."""
    timeline: list[dict[str, Any]] = []

    for event in lifecycle_events:
        timeline.append(
            {
                "kind": "lifecycle",
                "at": _iso(event.get("created_at")),
                "platform": event.get("platform"),
                "from_status": event.get("from_status"),
                "to_status": event.get("to_status"),
                "actor": event.get("actor"),
                "job_id": event.get("job_id"),
                "payload": event.get("payload") or {},
                "source": "post_lifecycle_events",
            }
        )

    if not lifecycle_events:
        created_at = _iso(hub.get("created_at"))
        updated_at = _iso(hub.get("updated_at"))
        timeline.append(
            {
                "kind": "synthetic",
                "at": created_at,
                "platform": hub.get("source_platform") or HUB_PLATFORM,
                "from_status": None,
                "to_status": "collected",
                "actor": "inferred",
                "job_id": None,
                "payload": {"note": "inferred from posts.created_at"},
                "source": "inferred",
            }
        )
        hub_status = hub.get("status")
        if hub_status and hub_status != "collected":
            timeline.append(
                {
                    "kind": "synthetic",
                    "at": updated_at,
                    "platform": HUB_PLATFORM,
                    "from_status": "collected",
                    "to_status": str(hub_status),
                    "actor": "inferred",
                    "job_id": None,
                    "payload": {"note": "inferred from posts.status/updated_at"},
                    "source": "inferred",
                }
            )
        for target in targets:
            timeline.append(
                {
                    "kind": "synthetic",
                    "at": _iso(target.get("updated_at")) or updated_at,
                    "platform": target.get("platform"),
                    "from_status": None,
                    "to_status": target.get("status"),
                    "actor": "inferred",
                    "job_id": None,
                    "payload": {
                        "target_id": target.get("id"),
                        "result": target.get("result") or {},
                        "note": "inferred from post_targets current state",
                    },
                    "source": "inferred",
                }
            )

    def sort_key(item: Mapping[str, Any]) -> tuple[str, str]:
        return (str(item.get("at") or ""), str(item.get("to_status") or ""))

    timeline.sort(key=sort_key)
    return timeline

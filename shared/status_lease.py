"""Reclaim stuck processing/publishing rows after a worker crash."""

from __future__ import annotations

from typing import Any

DEFAULT_STALE_PROCESSING_MINUTES = 15
DEFAULT_STALE_PUBLISHING_MINUTES = 5

_IDENT_RE = None


def _assert_ident(name: str) -> str:
    global _IDENT_RE
    if _IDENT_RE is None:
        import re

        _IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    if not _IDENT_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def reclaim_stale_sql(
    table: str,
    *,
    from_status: str,
    to_status: str,
    older_than_minutes: int,
) -> str:
    """Single-table lease reclaim. Bind (to_status, from_status, minutes)."""
    table = _assert_ident(table)
    return f"""
        UPDATE {table}
        SET status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE status = %s
          AND updated_at < CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
    """


def reclaim_source_processing_sql(table: str) -> str:
    """Return source processing → collected only when no hub posts row exists.

    Bind (minutes, source_platform).
    """
    table = _assert_ident(table)
    return f"""
        UPDATE {table} AS src
        SET status = 'collected', updated_at = CURRENT_TIMESTAMP
        WHERE src.status = 'processing'
          AND src.updated_at < CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
          AND NOT EXISTS (
            SELECT 1
            FROM posts p
            WHERE p.source_platform = %s
              AND p.source_id = src.id
          )
    """


async def reclaim_stale_status(
    cur: Any,
    table: str,
    *,
    from_status: str,
    to_status: str,
    older_than_minutes: int,
) -> int:
    await cur.execute(
        reclaim_stale_sql(
            table,
            from_status=from_status,
            to_status=to_status,
            older_than_minutes=older_than_minutes,
        ),
        (to_status, from_status, int(older_than_minutes)),
    )
    return int(cur.rowcount or 0)


async def reclaim_stale_publishing(
    cur: Any,
    table: str,
    *,
    older_than_minutes: int = DEFAULT_STALE_PUBLISHING_MINUTES,
) -> int:
    return await reclaim_stale_status(
        cur,
        table,
        from_status="publishing",
        to_status="ready",
        older_than_minutes=older_than_minutes,
    )


async def reclaim_stale_target_publishing(
    cur: Any,
    *,
    older_than_minutes: int = DEFAULT_STALE_PUBLISHING_MINUTES,
) -> int:
    """Lease reclaim on unified ``post_targets`` (slice 0+)."""
    from shared.db.post_model import POST_TARGETS_TABLE_NAME

    return await reclaim_stale_publishing(
        cur,
        POST_TARGETS_TABLE_NAME,
        older_than_minutes=older_than_minutes,
    )

"""SQL repository for unified ``posts`` / ``post_targets``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from shared.db.post_model import (
    POST_CONTENT_STATUS_VALUES,
    POST_PLATFORMS,
    POST_TARGET_STATUS_VALUES,
    POST_TARGETS_TABLE_NAME,
    PUBLISH_PLATFORMS,
)
from shared.post_adapt import normalize_network
from shared.status_lease import (
    DEFAULT_STALE_PROCESSING_MINUTES,
    DEFAULT_STALE_PUBLISHING_MINUTES,
    reclaim_stale_status,
    reclaim_stale_target_publishing,
)

_POSTS = "posts"
_TARGETS = POST_TARGETS_TABLE_NAME

INBOUND_INSERT_COLUMNS: tuple[str, ...] = (
    "user_id",
    "brand_id",
    "channel_id",
    "source_platform",
    "source_native_id",
    "domain",
    "url",
    "title",
    "author",
    "avatar",
    "post_date",
    "post_text",
    "screenshot",
    "images",
    "videos",
    "extras",
    "target_channels",
    "target_groups",
    "status",
)

LEGACY_FLAG_TO_PLATFORM: dict[str, str] = {
    "to_tg": "tg",
    "to_tw": "tw",
    "to_wp": "wp",
    "to_vk": "vk",
    "to_threads": "threads",
    "to_dzen": "dzen",
    "to_instagram": "instagram",
}

LEGACY_DESTINATION_FLAG_COLUMNS: tuple[str, ...] = tuple(LEGACY_FLAG_TO_PLATFORM.keys())

CLAIM_PROCESS_COLUMNS: tuple[str, ...] = (
    "id",
    "user_id",
    "source_platform",
    "source_native_id",
    "post_text",
    "images",
    "url",
    "extras",
    "platform_texts",
    "status",
)

CLAIM_PUBLISH_SELECT: str = """
SELECT
    t.id AS target_id,
    t.post_id,
    t.user_id,
    t.platform,
    t.status,
    t.publish_at,
    t.target_channels,
    t.target_groups,
    t.result,
    p.post_text,
    p.images,
    p.videos,
    p.title,
    p.url,
    p.extras,
    p.platform_texts,
    p.brand_id,
    p.channel_id
FROM post_targets t
JOIN posts p ON p.id = t.post_id
WHERE t.platform = %s
  AND t.status = %s
  AND (t.publish_at IS NULL OR t.publish_at <= CURRENT_TIMESTAMP)
"""


@dataclass
class InboundPostCreate:
    """Receive-an-object payload for inserting a hub post."""

    user_id: int
    source_platform: str
    post_text: str = ""
    brand_id: Optional[int] = None
    channel_id: Optional[int] = None
    source_native_id: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    screenshot: Optional[str] = None
    images: Sequence[Any] = field(default_factory=list)
    videos: Sequence[Any] = field(default_factory=list)
    extras: Mapping[str, Any] = field(default_factory=dict)
    target_channels: Sequence[Any] = field(default_factory=list)
    target_groups: Sequence[Any] = field(default_factory=list)
    status: str = "collected"
    target_platforms: Sequence[str] = field(default_factory=tuple)
    target_status: str = "pending"


@dataclass
class PublishResult:
    """Receive-an-object payload for finishing a claimed target."""

    target_id: int
    ok: bool
    result: Mapping[str, Any] = field(default_factory=dict)
    status: Optional[str] = None


class UnknownPlatformError(ValueError):
    """Platform is missing or not in the frozen contract."""


def require_content_platform(raw: str | None) -> str:
    platform = normalize_network(raw)
    if platform not in POST_PLATFORMS:
        raise UnknownPlatformError(f"Unknown source platform: {raw!r}")
    return platform


def require_publish_platform(raw: str | None) -> str:
    platform = normalize_network(raw)
    if platform not in PUBLISH_PLATFORMS:
        raise UnknownPlatformError(f"Unknown publish platform: {raw!r}")
    return platform


def require_content_status(raw: str) -> str:
    if raw not in POST_CONTENT_STATUS_VALUES:
        raise ValueError(f"Unknown post status: {raw!r}")
    return raw


def require_target_status(raw: str) -> str:
    if raw not in POST_TARGET_STATUS_VALUES:
        raise ValueError(f"Unknown target status: {raw!r}")
    return raw


def _json_param(value: Any, empty: str = "[]") -> str:
    if value is None:
        return empty
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _id_placeholders(count: int) -> str:
    if count < 1:
        raise ValueError("Need at least one id")
    return ", ".join(["%s"] * count)


def create_inbound_sql(payload: InboundPostCreate) -> tuple[str, tuple[Any, ...]]:
    require_content_platform(payload.source_platform)
    require_content_status(payload.status)
    columns = ", ".join(INBOUND_INSERT_COLUMNS)
    placeholders = ", ".join(["%s"] * len(INBOUND_INSERT_COLUMNS))
    sql = (
        f"INSERT INTO {_POSTS} ({columns}) VALUES ({placeholders}) "
        "RETURNING id, user_id, source_platform, status"
    )
    params = (
        payload.user_id,
        payload.brand_id,
        payload.channel_id,
        require_content_platform(payload.source_platform),
        payload.source_native_id,
        payload.domain,
        payload.url,
        payload.title,
        payload.author,
        payload.avatar,
        payload.post_date,
        payload.post_text,
        payload.screenshot,
        _json_param(payload.images, "[]"),
        _json_param(payload.videos, "[]"),
        _json_param(dict(payload.extras), "{}"),
        _json_param(list(payload.target_channels), "[]"),
        _json_param(list(payload.target_groups), "[]"),
        payload.status,
    )
    return sql, params


def ensure_targets_sql(
    *,
    post_id: int,
    user_id: int,
    platforms: Sequence[str],
    status: str = "pending",
    target_channels: Sequence[Any] | None = None,
    target_groups: Sequence[Any] | None = None,
) -> tuple[str, list[Any]]:
    require_target_status(status)
    unique_platforms: list[str] = []
    for raw in platforms:
        platform = require_publish_platform(raw)
        if platform not in unique_platforms:
            unique_platforms.append(platform)
    if not unique_platforms:
        raise ValueError("Need at least one publish platform")
    values_sql = ", ".join(["(%s, %s, %s, %s, %s::jsonb, %s::jsonb)"] * len(unique_platforms))
    sql = f"""
INSERT INTO {_TARGETS} (post_id, user_id, platform, status, target_channels, target_groups)
VALUES {values_sql}
ON CONFLICT (post_id, platform) DO UPDATE
SET status = EXCLUDED.status,
    target_channels = COALESCE(EXCLUDED.target_channels, {_TARGETS}.target_channels),
    target_groups = COALESCE(EXCLUDED.target_groups, {_TARGETS}.target_groups),
    updated_at = CURRENT_TIMESTAMP
WHERE {_TARGETS}.status IN ('pending', 'ready')
RETURNING id, post_id, platform, status
""".strip()
    params: list[Any] = []
    channels = _json_param(list(target_channels or []), "[]")
    groups = _json_param(list(target_groups or []), "[]")
    for platform in unique_platforms:
        params.extend([post_id, user_id, platform, status, channels, groups])
    return sql, params


def claim_process_select_sql(*, limit: int) -> tuple[str, tuple[Any, ...]]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    columns = ", ".join(CLAIM_PROCESS_COLUMNS)
    sql = f"""
SELECT {columns}
FROM {_POSTS}
WHERE status IN ('collected', 'created')
ORDER BY created_at
LIMIT %s
FOR UPDATE SKIP LOCKED
""".strip()
    return sql, (int(limit),)


def mark_posts_status_sql(post_ids: Sequence[int], status: str) -> tuple[str, tuple[Any, ...]]:
    require_content_status(status)
    placeholders = _id_placeholders(len(post_ids))
    sql = f"""
UPDATE {_POSTS}
SET status = %s, updated_at = CURRENT_TIMESTAMP
WHERE id IN ({placeholders})
""".strip()
    return sql, (status, *tuple(int(item) for item in post_ids))


def claim_publish_select_sql(
    *,
    platform: str,
    limit: int,
    user_id: Optional[int] = None,
) -> tuple[str, tuple[Any, ...]]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    require_publish_platform(platform)
    sql = CLAIM_PUBLISH_SELECT.rstrip()
    params: list[Any] = [require_publish_platform(platform), "ready"]
    if user_id is not None:
        sql += "\n  AND t.user_id = %s"
        params.append(int(user_id))
    sql += """
ORDER BY COALESCE(t.publish_at, t.created_at) ASC NULLS LAST
LIMIT %s
FOR UPDATE OF t SKIP LOCKED
"""
    params.append(int(limit))
    return sql.strip(), tuple(params)


def mark_targets_status_sql(
    target_ids: Sequence[int],
    status: str,
) -> tuple[str, tuple[Any, ...]]:
    require_target_status(status)
    placeholders = _id_placeholders(len(target_ids))
    sql = f"""
UPDATE {_TARGETS}
SET status = %s, updated_at = CURRENT_TIMESTAMP
WHERE id IN ({placeholders})
""".strip()
    return sql, (status, *tuple(int(item) for item in target_ids))


def resolve_publish_platforms(
    *,
    legacy_flags: Mapping[str, Any],
    process_services: Any = None,
    source_platform: str | None = None,
) -> list[str]:
    """Map to_* / process_services / TG default to publish platform keys."""
    found: list[str] = []

    def _add(platform: str) -> None:
        if platform not in found and platform in PUBLISH_PLATFORMS:
            found.append(platform)

    for flag, platform in LEGACY_FLAG_TO_PLATFORM.items():
        if legacy_flags.get(flag):
            _add(platform)

    if found:
        return found

    services = process_services or []
    if isinstance(services, str):
        try:
            services = json.loads(services)
        except (json.JSONDecodeError, TypeError):
            services = []
    if not isinstance(services, list):
        services = []
    for item in services:
        _add(normalize_network(str(item)))

    if found:
        return found

    source = normalize_network(source_platform)
    if source == "tg":
        _add("tg")
    return found


def flags_from_platforms(platforms: Sequence[str]) -> dict[str, bool]:
    enabled = set(platforms)
    return {
        flag: platform in enabled
        for flag, platform in LEGACY_FLAG_TO_PLATFORM.items()
    }


UI_TARGET_COLUMNS: tuple[str, ...] = (
    "id",
    "post_id",
    "user_id",
    "platform",
    "status",
    "publish_at",
    "target_channels",
    "target_groups",
    "result",
    "post_text",
    "images",
    "videos",
    "title",
    "url",
    "author",
    "domain",
    "screenshot",
    "extras",
    "brand_id",
    "channel_id",
    "source_platform",
    "created_at",
    "updated_at",
)

_UI_TARGET_FROM = f"""
FROM {_TARGETS} t
JOIN {_POSTS} p ON p.id = t.post_id
""".strip()

_UI_TARGET_SELECT = f"""
SELECT
    t.id,
    p.id AS post_id,
    t.user_id,
    t.platform,
    t.status,
    t.publish_at,
    COALESCE(t.target_channels, p.target_channels) AS target_channels,
    COALESCE(t.target_groups, p.target_groups) AS target_groups,
    t.result,
    p.post_text,
    p.images,
    p.videos,
    p.title,
    p.url,
    p.author,
    p.domain,
    p.screenshot,
    p.extras,
    p.brand_id,
    p.channel_id,
    p.source_platform,
    p.created_at,
    t.updated_at
{_UI_TARGET_FROM}
""".strip()


def list_targets_sql(
    *,
    user_id: int,
    platform: str,
    limit: int,
    offset: int,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> tuple[str, tuple[Any, ...]]:
    require_publish_platform(platform)
    conditions = ["t.user_id = %s", "t.platform = %s", "(t.status IS NULL OR t.status != 'deleted')"]
    params: list[Any] = [int(user_id), require_publish_platform(platform)]
    if status:
        require_target_status(status)
        conditions.append("t.status = %s")
        params.append(status)
    if date_from:
        conditions.append("COALESCE(t.publish_at, p.created_at) >= %s::timestamptz")
        params.append(date_from)
    if date_to:
        conditions.append("COALESCE(t.publish_at, p.created_at) <= %s::timestamptz")
        params.append(date_to)
    params.extend([int(limit), int(offset)])
    sql = f"""
{_UI_TARGET_SELECT}
WHERE {" AND ".join(conditions)}
ORDER BY COALESCE(t.publish_at, p.created_at) DESC
LIMIT %s OFFSET %s
""".strip()
    return sql, tuple(params)


def get_target_sql(
    *,
    user_id: int,
    target_id: int,
    platform: Optional[str] = None,
) -> tuple[str, tuple[Any, ...]]:
    conditions = ["t.user_id = %s", "t.id = %s"]
    params: list[Any] = [int(user_id), int(target_id)]
    if platform:
        conditions.append("t.platform = %s")
        params.append(require_publish_platform(platform))
    sql = f"""
{_UI_TARGET_SELECT}
WHERE {" AND ".join(conditions)}
LIMIT 1
""".strip()
    return sql, tuple(params)


def _ui_target_row(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    row["_queue"] = "targets"
    row["_target_id"] = int(item["id"])
    row["_post_id"] = int(item["post_id"])
    extras = row.get("extras")
    if isinstance(extras, dict) and extras.get("attachments") is not None:
        row["attachments"] = extras.get("attachments")
    row.update(flags_from_platforms([str(item.get("platform") or "")]))
    return row


def save_processed_sql(
    *,
    post_id: int,
    text: str,
    images: Sequence[Any],
    platform_texts: Mapping[str, Any],
    status: str,
) -> tuple[str, tuple[Any, ...]]:
    require_content_status(status)
    sql = f"""
UPDATE {_POSTS}
SET post_text = %s,
    images = %s,
    platform_texts = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s
  AND status = 'processing'
""".strip()
    return sql, (
        text,
        _json_param(images, "[]"),
        _json_param(dict(platform_texts), "{}"),
        status,
        int(post_id),
    )


def publish_result_sql(payload: PublishResult) -> tuple[str, tuple[Any, ...]]:
    if payload.status is not None:
        status = require_target_status(payload.status)
    else:
        status = "published" if payload.ok else "failed"
    patch = dict(payload.result)
    if status == "published":
        patch.pop("error", None)
    elif status == "failed" and "error" not in patch:
        patch["error"] = "publish_failed"
    sql = f"""
UPDATE {_TARGETS}
SET status = %s,
    result = COALESCE(result, '{{}}'::jsonb) || %s::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s
  AND status = 'publishing'
RETURNING id, post_id, platform, status, result
""".strip()
    return sql, (status, json.dumps(patch, ensure_ascii=False), int(payload.target_id))


def _rows_as_dicts(cur: Any, rows: Sequence[Sequence[Any]], columns: Sequence[str]) -> list[dict[str, Any]]:
    _ = cur
    return [dict(zip(columns, row)) for row in rows]


class PostsRepository:
    """Cursor-bound operations for the unified post queue."""

    def __init__(self, cur: Any) -> None:
        self._cur = cur

    async def create_inbound(self, payload: InboundPostCreate) -> dict[str, Any]:
        sql, params = create_inbound_sql(payload)
        await self._cur.execute(sql, params)
        row = await self._cur.fetchone()
        if row is None:
            raise RuntimeError("INSERT posts did not return a row")
        created = _rows_as_dicts(self._cur, [row], ("id", "user_id", "source_platform", "status"))[0]
        created["targets"] = []
        if payload.target_platforms:
            created["targets"] = await self.ensure_targets(
                post_id=int(created["id"]),
                user_id=int(payload.user_id),
                platforms=payload.target_platforms,
                status=payload.target_status,
                target_channels=payload.target_channels,
                target_groups=payload.target_groups,
            )
        return created

    async def ensure_targets(
        self,
        *,
        post_id: int,
        user_id: int,
        platforms: Sequence[str],
        status: str = "pending",
        target_channels: Sequence[Any] | None = None,
        target_groups: Sequence[Any] | None = None,
    ) -> list[dict[str, Any]]:
        sql, params = ensure_targets_sql(
            post_id=post_id,
            user_id=user_id,
            platforms=platforms,
            status=status,
            target_channels=target_channels,
            target_groups=target_groups,
        )
        await self._cur.execute(sql, params)
        rows = await self._cur.fetchall()
        return _rows_as_dicts(self._cur, rows or (), ("id", "post_id", "platform", "status"))

    async def claim_process(
        self,
        *,
        limit: int,
        stale_minutes: int = DEFAULT_STALE_PROCESSING_MINUTES,
    ) -> list[dict[str, Any]]:
        await reclaim_stale_status(
            self._cur,
            _POSTS,
            from_status="processing",
            to_status="collected",
            older_than_minutes=stale_minutes,
        )
        sql, params = claim_process_select_sql(limit=limit)
        await self._cur.execute(sql, params)
        rows = await self._cur.fetchall()
        if not rows:
            return []
        records = _rows_as_dicts(self._cur, rows, CLAIM_PROCESS_COLUMNS)
        ids = [int(item["id"]) for item in records]
        update_sql, update_params = mark_posts_status_sql(ids, "processing")
        await self._cur.execute(update_sql, update_params)
        for item in records:
            item["status"] = "processing"
        return records

    async def complete_processing(self, post_ids: Sequence[int], status: str) -> None:
        if status not in ("ready", "review", "deleted"):
            raise ValueError(f"complete_processing cannot set {status!r}")
        if not post_ids:
            return
        sql, params = mark_posts_status_sql(post_ids, status)
        await self._cur.execute(sql, params)

    async def save_processed(
        self,
        *,
        post_id: int,
        text: str,
        images: Sequence[Any],
        platform_texts: Mapping[str, Any],
        status: str,
    ) -> None:
        sql, params = save_processed_sql(
            post_id=post_id,
            text=text,
            images=images,
            platform_texts=platform_texts,
            status=status,
        )
        await self._cur.execute(sql, params)

    async def set_posts_status(self, post_ids: Sequence[int], status: str) -> None:
        if not post_ids:
            return
        sql, params = mark_posts_status_sql(post_ids, status)
        await self._cur.execute(sql, params)

    async def claim_publish(
        self,
        *,
        platform: str,
        limit: int,
        user_id: Optional[int] = None,
        stale_minutes: int = DEFAULT_STALE_PUBLISHING_MINUTES,
    ) -> list[dict[str, Any]]:
        await reclaim_stale_target_publishing(self._cur, older_than_minutes=stale_minutes)
        sql, params = claim_publish_select_sql(platform=platform, limit=limit, user_id=user_id)
        await self._cur.execute(sql, params)
        rows = await self._cur.fetchall()
        if not rows:
            return []
        column_names = (
            "target_id",
            "post_id",
            "user_id",
            "platform",
            "status",
            "publish_at",
            "target_channels",
            "target_groups",
            "result",
            "post_text",
            "images",
            "videos",
            "title",
            "url",
            "extras",
            "platform_texts",
            "brand_id",
            "channel_id",
        )
        records = _rows_as_dicts(self._cur, rows, column_names)
        ids = [int(item["target_id"]) for item in records]
        update_sql, update_params = mark_targets_status_sql(ids, "publishing")
        await self._cur.execute(update_sql, update_params)
        for item in records:
            item["status"] = "publishing"
        return records

    async def apply_publish_result(self, payload: PublishResult) -> Optional[dict[str, Any]]:
        sql, params = publish_result_sql(payload)
        await self._cur.execute(sql, params)
        row = await self._cur.fetchone()
        if row is None:
            return None
        return _rows_as_dicts(
            self._cur,
            [row],
            ("id", "post_id", "platform", "status", "result"),
        )[0]

    async def list_targets(
        self,
        *,
        user_id: int,
        platform: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        sql, params = list_targets_sql(
            user_id=user_id,
            platform=platform,
            limit=limit,
            offset=offset,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
        await self._cur.execute(sql, params)
        rows = await self._cur.fetchall()
        return [_ui_target_row(item) for item in _rows_as_dicts(self._cur, rows, UI_TARGET_COLUMNS)]

    async def get_target(self, *, user_id: int, target_id: int, platform: Optional[str] = None) -> Optional[dict[str, Any]]:
        sql, params = get_target_sql(user_id=user_id, target_id=target_id, platform=platform)
        await self._cur.execute(sql, params)
        row = await self._cur.fetchone()
        if row is None:
            return None
        return _ui_target_row(_rows_as_dicts(self._cur, [row], UI_TARGET_COLUMNS)[0])

    async def update_target(
        self,
        *,
        user_id: int,
        target_id: int,
        platform: Optional[str] = None,
        post_text: Optional[str] = None,
        images: Optional[Sequence[Any]] = None,
        videos: Optional[Sequence[Any]] = None,
        title: Optional[str] = None,
        extras: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
        publish_at: Any = None,
        clear_publish_at: bool = False,
        target_channels: Optional[Sequence[Any]] = None,
        target_groups: Optional[Sequence[Any]] = None,
    ) -> Optional[dict[str, Any]]:
        current = await self.get_target(user_id=user_id, target_id=target_id, platform=platform)
        if current is None:
            return None
        post_id = int(current["post_id"])
        hub_sets: list[str] = []
        hub_params: list[Any] = []
        if post_text is not None:
            hub_sets.append("post_text = %s")
            hub_params.append(post_text)
        if images is not None:
            hub_sets.append("images = %s")
            hub_params.append(_json_param(list(images), "[]"))
        if videos is not None:
            hub_sets.append("videos = %s")
            hub_params.append(_json_param(list(videos), "[]"))
        if title is not None:
            hub_sets.append("title = %s")
            hub_params.append(title)
        if extras is not None:
            hub_sets.append("extras = COALESCE(extras, '{}'::jsonb) || %s::jsonb")
            hub_params.append(_json_param(dict(extras), "{}"))
        target_sets: list[str] = []
        target_params: list[Any] = []
        if status is not None:
            if status in POST_TARGET_STATUS_VALUES:
                target_sets.append("status = %s")
                target_params.append(status)
            elif status in POST_CONTENT_STATUS_VALUES:
                hub_sets.append("status = %s")
                hub_params.append(status)
            else:
                require_target_status(status)
        if hub_sets:
            hub_params.append(post_id)
            await self._cur.execute(
                f"UPDATE {_POSTS} SET {', '.join(hub_sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                hub_params,
            )
        if clear_publish_at:
            target_sets.append("publish_at = NULL")
        elif publish_at is not None:
            target_sets.append("publish_at = %s")
            target_params.append(publish_at)
        if target_channels is not None:
            target_sets.append("target_channels = %s::jsonb")
            target_params.append(_json_param(list(target_channels), "[]"))
        if target_groups is not None:
            target_sets.append("target_groups = %s::jsonb")
            target_params.append(_json_param(list(target_groups), "[]"))
        if target_sets:
            target_params.extend([int(target_id), int(user_id)])
            await self._cur.execute(
                f"""
                UPDATE {_TARGETS}
                SET {", ".join(target_sets)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                """.strip(),
                target_params,
            )
        return await self.get_target(user_id=user_id, target_id=target_id, platform=platform)

    async def set_target_publish_at(self, target_id: int, publish_at: Any) -> None:
        await self._cur.execute(
            f"UPDATE {_TARGETS} SET publish_at = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (publish_at, int(target_id)),
        )

    async def list_hub(
        self,
        *,
        user_id: int,
        source_platform: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        require_content_platform(source_platform)
        await self._cur.execute(
            f"""
            SELECT id, user_id, source_platform, post_text, images, url, title, status,
                   target_channels, target_groups, extras, brand_id, channel_id,
                   created_at, updated_at, post_date, screenshot
            FROM {_POSTS}
            WHERE user_id = %s AND source_platform = %s
              AND (status IS NULL OR status != 'deleted')
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (int(user_id), source_platform, int(limit), int(offset)),
        )
        rows = await self._cur.fetchall()
        return _rows_as_dicts(
            self._cur,
            rows,
            (
                "id",
                "user_id",
                "source_platform",
                "post_text",
                "images",
                "url",
                "title",
                "status",
                "target_channels",
                "target_groups",
                "extras",
                "brand_id",
                "channel_id",
                "created_at",
                "updated_at",
                "post_date",
                "screenshot",
            ),
        )

    async def get_hub(self, *, user_id: int, post_id: int) -> Optional[dict[str, Any]]:
        await self._cur.execute(
            f"SELECT * FROM {_POSTS} WHERE user_id = %s AND id = %s",
            (int(user_id), int(post_id)),
        )
        row = await self._cur.fetchone()
        if row is None:
            return None
        names = [col.name for col in self._cur.description]
        return dict(zip(names, row))

    async def mark_hub_deleted(self, *, user_id: int, post_id: int) -> Optional[dict[str, Any]]:
        await self._cur.execute(
            f"""
            UPDATE {_POSTS}
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND id = %s
            RETURNING *
            """,
            (int(user_id), int(post_id)),
        )
        row = await self._cur.fetchone()
        if row is None:
            return None
        names = [col.name for col in self._cur.description]
        return dict(zip(names, row))


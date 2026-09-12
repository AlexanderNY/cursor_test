"""Create/list/update unified posts + post_targets for Core APIs."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional, Sequence

from database import get_db_connection, release_db_connection
from services.quota_service import ensure_monthly_post_quota
from shared.db.post_model import PUBLISH_PLATFORMS
from shared.db.posts_repo import (
    InboundPostCreate,
    PostsRepository,
    flags_from_platforms,
    resolve_publish_platforms,
)
from shared.queue_wakeup import wake_process_http


async def _wake_processor(status: str) -> None:
    if status not in ("collected", "created"):
        return
    try:
        from config import settings

        await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
    except Exception:
        pass


def platforms_from_flags(
    *,
    source_platform: str,
    to_tg: bool = False,
    to_tw: bool = False,
    to_wp: bool = False,
    to_vk: bool = False,
    to_threads: bool = False,
    to_dzen: bool = False,
    to_instagram: bool = False,
) -> list[str]:
    return resolve_publish_platforms(
        legacy_flags={
            "to_tg": to_tg,
            "to_tw": to_tw,
            "to_wp": to_wp,
            "to_vk": to_vk,
            "to_threads": to_threads,
            "to_dzen": to_dzen,
            "to_instagram": to_instagram,
        },
        source_platform=source_platform,
    )


async def create_unified_post(
    *,
    user_id: int,
    source_platform: str,
    text: str,
    images: Optional[Sequence[Any]] = None,
    videos: Optional[Sequence[Any]] = None,
    title: Optional[str] = None,
    url: Optional[str] = None,
    extras: Optional[Mapping[str, Any]] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    target_channels: Optional[Sequence[Any]] = None,
    target_groups: Optional[Sequence[Any]] = None,
    publish_at: Any = None,
    status: str = "collected",
    target_status: Optional[str] = None,
    skip_quota: bool = False,
    to_tg: bool = False,
    to_tw: bool = False,
    to_wp: bool = False,
    to_vk: bool = False,
    to_threads: bool = False,
    to_dzen: bool = False,
    to_instagram: bool = False,
    return_platform: Optional[str] = None,
) -> dict[str, Any]:
    platforms = platforms_from_flags(
        source_platform=source_platform,
        to_tg=to_tg,
        to_tw=to_tw,
        to_wp=to_wp,
        to_vk=to_vk,
        to_threads=to_threads,
        to_dzen=to_dzen,
        to_instagram=to_instagram,
    )
    hub_status = "ready" if status == "ready" else status
    resolved_target_status = target_status
    if resolved_target_status is None:
        resolved_target_status = "ready" if hub_status == "ready" else "pending"
    conn = await get_db_connection()
    try:
        if not skip_quota:
            await ensure_monthly_post_quota(user_id, conn=conn)
        async with conn.cursor() as cur:
            repo = PostsRepository(cur)
            created = await repo.create_inbound(
                InboundPostCreate(
                    user_id=user_id,
                    source_platform=source_platform,
                    post_text=text,
                    title=title,
                    url=url,
                    images=list(images or []),
                    videos=list(videos or []),
                    extras=dict(extras or {}),
                    brand_id=brand_id,
                    channel_id=channel_id,
                    target_channels=list(target_channels or []),
                    target_groups=list(target_groups or []),
                    status=hub_status,
                    target_platforms=tuple(platforms),
                    target_status=resolved_target_status,
                )
            )
            prefer = return_platform or source_platform
            target = None
            for item in created.get("targets") or []:
                if item.get("platform") == prefer:
                    target = item
                    break
            if target is None and created.get("targets"):
                target = created["targets"][0]
            if target and publish_at is not None:
                await repo.set_target_publish_at(int(target["id"]), publish_at)
            if target:
                row = await repo.get_target(user_id=user_id, target_id=int(target["id"]))
            else:
                row = await repo.get_hub(user_id=user_id, post_id=int(created["id"]))
                if row is not None:
                    row.update(flags_from_platforms(platforms))
            if not row:
                raise RuntimeError("unified post create did not return a row")
            await _wake_processor(hub_status)
            return row
    finally:
        await release_db_connection(conn)


async def list_platform_posts(
    *,
    user_id: int,
    platform: str,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            if platform in PUBLISH_PLATFORMS:
                return await PostsRepository(cur).list_targets(
                    user_id=user_id,
                    platform=platform,
                    limit=limit,
                    offset=offset,
                    status=status,
                    date_from=date_from,
                    date_to=date_to,
                )
            return await PostsRepository(cur).list_hub(
                user_id=user_id,
                source_platform=platform,
                limit=limit,
                offset=offset,
            )
    finally:
        await release_db_connection(conn)


async def get_platform_post(
    *,
    user_id: int,
    post_id: int,
    platform: str,
) -> Optional[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            repo = PostsRepository(cur)
            if platform in PUBLISH_PLATFORMS:
                row = await repo.get_target(user_id=user_id, target_id=post_id, platform=platform)
                if row:
                    return row
            return await repo.get_hub(user_id=user_id, post_id=post_id)
    finally:
        await release_db_connection(conn)


async def update_platform_post(
    *,
    user_id: int,
    post_id: int,
    platform: str,
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
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            repo = PostsRepository(cur)
            if platform in PUBLISH_PLATFORMS:
                return await repo.update_target(
                    user_id=user_id,
                    target_id=post_id,
                    platform=platform,
                    post_text=post_text,
                    images=images,
                    videos=videos,
                    title=title,
                    extras=extras,
                    status=status,
                    publish_at=publish_at,
                    clear_publish_at=clear_publish_at,
                    target_channels=target_channels,
                    target_groups=target_groups,
                )
            if status == "deleted":
                return await repo.mark_hub_deleted(user_id=user_id, post_id=post_id)
            sets: list[str] = []
            params: list[Any] = []
            if post_text is not None:
                sets.append("post_text = %s")
                params.append(post_text)
            if images is not None:
                sets.append("images = %s")
                params.append(json.dumps(list(images)))
            if title is not None:
                sets.append("title = %s")
                params.append(title)
            if status is not None:
                sets.append("status = %s")
                params.append(status)
            if not sets:
                return await repo.get_hub(user_id=user_id, post_id=post_id)
            params.extend([user_id, post_id])
            await cur.execute(
                f"""
                UPDATE posts SET {", ".join(sets)}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND id = %s
                RETURNING *
                """,
                params,
            )
            row = await cur.fetchone()
            if row is None:
                return None
            names = [col.name for col in cur.description]
            return dict(zip(names, row))
    finally:
        await release_db_connection(conn)

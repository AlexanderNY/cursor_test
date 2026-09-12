"""Сервис для сбора постов из WordPress (brand-channel + legacy fallback)."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from config import settings
from database import get_db_connection, release_db_connection
from shared.db.bot_queue import dest_flags_to_platforms
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http
from services.brand_channel_flow import (
    list_wp_collect_channels,
    publish_targets_to_destination_fields,
    resolve_credentials_for_site,
    resolve_publish_targets,
)
from services.channel_counter import bump_channel_counter
from services.wordpress_client import WordPressClient
from shared.text_conditions import should_save_text

logger = logging.getLogger(__name__)


class CollectService:
    """Сбор постов из WordPress в wp_posts через brand channels (+ legacy)."""

    async def collect_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        collected_count = 0
        failed_count = 0
        errors: list[dict[str, Any]] = []
        limit_per_pass = settings.COLLECT_POSTS_LIMIT
        polled: Set[Tuple[int, str]] = set()  # (user_id, normalized site)

        channels = await list_wp_collect_channels(user_id)
        for channel in channels:
            if collected_count >= limit_per_pass:
                break
            uid = int(channel["user_id"])
            site_url = str(channel.get("external_id") or "").strip()
            if not site_url:
                continue
            key = (uid, site_url.rstrip("/").lower())
            if key in polled:
                continue

            creds = await resolve_credentials_for_site(uid, site_url)
            if not creds:
                errors.append(
                    {
                        "user_id": uid,
                        "channel_id": channel.get("id"),
                        "error": "Incomplete WordPress credentials for brand channel site",
                    }
                )
                failed_count += 1
                continue

            dest = await self._dest_for_channel(channel)
            try:
                n = await self._collect_from_site(
                    user_id=uid,
                    site_url=creds["site_url"],
                    username=creds["username"],
                    app_password=creds["app_password"],
                    remaining=limit_per_pass - collected_count,
                    dest=dest,
                    save_conditions=channel.get("save_conditions") or [],
                    conditions_mode=channel.get("conditions_mode") or "any_of",
                    channel_id=channel.get("id"),
                )
                collected_count += n
                polled.add(key)
            except Exception as exc:
                error_msg = f"Error collecting channel_id={channel.get('id')}: {exc!s}"
                logger.error(error_msg)
                errors.append(
                    {
                        "user_id": uid,
                        "channel_id": channel.get("id"),
                        "error": error_msg,
                    }
                )
                failed_count += 1

        # Legacy fallback: wp_collect_profile + wp_collect_sites
        if collected_count < limit_per_pass:
            legacy = await self._collect_legacy(
                user_id=user_id,
                remaining=limit_per_pass - collected_count,
                polled=polled,
            )
            collected_count += int(legacy.get("collected", 0))
            failed_count += int(legacy.get("failed", 0))
            errors.extend(legacy.get("errors") or [])

        if collected_count > 0:
            await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
        return {
            "collected": collected_count,
            "failed": failed_count,
            "errors": errors,
        }

    async def _dest_for_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = channel.get("brand_id")
        target_ids = channel.get("publish_targets") or []
        if not brand_id or not target_ids:
            return {}
        resolved = await resolve_publish_targets(int(brand_id), target_ids)
        return publish_targets_to_destination_fields(resolved)

    async def _collect_from_site(
        self,
        *,
        user_id: int,
        site_url: str,
        username: str,
        app_password: str,
        remaining: int,
        dest: Optional[Dict[str, Any]] = None,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
        channel_id: Optional[int] = None,
    ) -> int:
        if remaining <= 0:
            return 0

        wp_client = WordPressClient(
            site_url=site_url,
            username=username,
            app_password=app_password,
        )
        dest = dest or {}
        collected = 0
        page = 1
        per_page = 20

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                while collected < remaining:
                    result = await wp_client.get_posts(
                        per_page=per_page,
                        page=page,
                        status="publish",
                    )
                    posts = result.get("posts", [])
                    if not posts:
                        break

                    for wp_post in posts:
                        if collected >= remaining:
                            break

                        wp_post_link = wp_post.get("link", "")
                        title = (
                            wp_post.get("title", {}).get("rendered", "")
                            if isinstance(wp_post.get("title"), dict)
                            else wp_post.get("title", "")
                        )
                        content = (
                            wp_post.get("content", {}).get("rendered", "")
                            if isinstance(wp_post.get("content"), dict)
                            else wp_post.get("content", "")
                        )
                        text_for_filter = f"{title}\n{content}"
                        if not should_save_text(
                            text_for_filter or "",
                            save_conditions or [],
                            conditions_mode or "any_of",
                        ):
                            continue

                        await cur.execute(
                            """
                            SELECT id FROM posts
                            WHERE user_id = %s AND source_platform = 'wp' AND url = %s
                            """,
                            (user_id, wp_post_link),
                        )
                        if await cur.fetchone():
                            continue

                        post_date = None
                        if wp_post.get("date"):
                            try:
                                post_date = datetime.fromisoformat(
                                    wp_post["date"].replace("Z", "+00:00")
                                )
                            except ValueError:
                                post_date = None

                        author_name = None
                        if wp_post.get("_embedded") and wp_post["_embedded"].get("author"):
                            author_name = wp_post["_embedded"]["author"][0].get("name")

                        platforms = dest_flags_to_platforms(dest)
                        created = await PostsRepository(cur).create_inbound(
                            InboundPostCreate(
                                user_id=user_id,
                                source_platform="wp",
                                post_text=content,
                                title=title,
                                author=author_name,
                                domain=site_url,
                                url=wp_post_link,
                                post_date=post_date,
                                source_native_id=wp_post_link,
                                target_channels=dest.get("target_channels") or [],
                                target_groups=dest.get("target_groups") or [],
                                target_platforms=platforms,
                                target_status="pending",
                            )
                        )
                        post_row_id = int(created["id"])
                        collected += 1
                        await bump_channel_counter(
                            user_id,
                            channel_id=channel_id,
                            network="wp",
                            external_id=site_url,
                            received=1,
                            direction="collected",
                            platform="wp",
                            post_id=post_row_id,
                            metadata={"text_preview": (title or "")[:120]},
                        )

                    total_pages = result.get("total_pages", 0)
                    if page >= total_pages:
                        break
                    page += 1

                await conn.commit()
        finally:
            await release_db_connection(conn)

        if collected > 0:
            logger.info(
                "Collected %d posts from WordPress site=%s user_id=%s channel_id=%s",
                collected,
                site_url,
                user_id,
                channel_id,
            )
        return collected

    async def _collect_legacy(
        self,
        *,
        user_id: Optional[int],
        remaining: int,
        polled: Set[Tuple[int, str]],
    ) -> Dict[str, Any]:
        if remaining <= 0:
            return {"collected": 0, "failed": 0, "errors": []}

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                query = """
                    SELECT
                        cp.user_id,
                        cs.site_url,
                        pub.username,
                        pub.app_password
                    FROM wp_collect_profile cp
                    JOIN wp_publish_profile pub ON pub.user_id = cp.user_id
                    LEFT JOIN wp_collect_sites cs ON cs.profile_id = cp.id
                    WHERE cp.collect_enabled = TRUE
                """
                params: tuple[Any, ...] = ()
                if user_id is not None:
                    query += " AND cp.user_id = %s"
                    params = (user_id,)

                await cur.execute(query, params)
                rows = await cur.fetchall()
                if not rows:
                    return {"collected": 0, "failed": 0, "errors": []}

                columns = [col.name for col in cur.description]
        finally:
            await release_db_connection(conn)

        collected_count = 0
        failed_count = 0
        errors: list[dict[str, Any]] = []

        for row in rows:
            if collected_count >= remaining:
                break
            record = dict(zip(columns, row))
            uid = int(record["user_id"])
            site_url = (record.get("site_url") or "").strip()
            username = record.get("username")
            app_password = record.get("app_password")
            if not site_url or not username or not app_password:
                errors.append(
                    {
                        "user_id": uid,
                        "error": "Incomplete WordPress collect credentials or site_url",
                    }
                )
                failed_count += 1
                continue

            key = (uid, site_url.rstrip("/").lower())
            if key in polled:
                continue

            try:
                n = await self._collect_from_site(
                    user_id=uid,
                    site_url=site_url,
                    username=username,
                    app_password=app_password,
                    remaining=remaining - collected_count,
                    dest={"to_wp": True},
                )
                collected_count += n
                polled.add(key)
            except Exception as exc:
                error_msg = f"Error processing user_id={uid}: {exc!s}"
                logger.error(error_msg)
                errors.append({"user_id": uid, "error": error_msg})
                failed_count += 1

        return {
            "collected": collected_count,
            "failed": failed_count,
            "errors": errors,
        }


collect_service = CollectService()

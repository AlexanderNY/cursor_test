"""Сервис для публикации постов в WordPress (brand-channel aware)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config import settings
from database import get_db_connection, release_db_connection
from services.brand_channel_flow import (
    list_wp_publish_channels,
    load_wp_publish_profile,
    post_target_sites,
    resolve_credentials_for_site,
    site_urls_match,
)
from services.channel_counter import bump_channel_counter
from services.wordpress_client import WordPressClient

logger = logging.getLogger(__name__)


class PublishService:
    """Публикация постов из wp_posts в WordPress по brand channel / target_channels."""

    async def publish_pending_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                limit = settings.PUBLISH_POSTS_LIMIT
                if user_id:
                    await cur.execute(
                        """
                        SELECT * FROM wp_posts
                        WHERE user_id = %s
                          AND status = 'ready'
                          AND to_wp = TRUE
                        ORDER BY created_at ASC
                        LIMIT %s
                        """,
                        (user_id, limit),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT * FROM wp_posts
                        WHERE status = 'ready'
                          AND to_wp = TRUE
                        ORDER BY created_at ASC
                        LIMIT %s
                        """,
                        (limit,),
                    )

                rows = await cur.fetchall()
                if not rows:
                    return {"published": 0, "failed": 0, "errors": []}

                columns = [col.name for col in cur.description]
                published_count = 0
                failed_count = 0
                errors: list[dict[str, Any]] = []

                posts_by_user: Dict[int, List[Dict[str, Any]]] = {}
                for row in rows:
                    post = dict(zip(columns, row))
                    uid = int(post["user_id"])
                    posts_by_user.setdefault(uid, []).append(post)

                for uid, posts in posts_by_user.items():
                    publish_channels = await list_wp_publish_channels(uid)
                    for post in posts:
                        try:
                            sites = await self._resolve_sites_for_post(
                                uid, post, publish_channels
                            )
                            if not sites:
                                await self._update_post_status(
                                    cur,
                                    post["id"],
                                    "failed",
                                    "No WordPress publish target (brand channel or profile)",
                                )
                                failed_count += 1
                                continue

                            last_link = ""
                            ok_any = False
                            site_errors: list[str] = []

                            for site_info in sites:
                                site_url = site_info["site_url"]
                                channel_id = site_info.get("channel_id")
                                creds = await resolve_credentials_for_site(uid, site_url)
                                if not creds:
                                    site_errors.append(
                                        f"No credentials for site {site_url}"
                                    )
                                    continue

                                title = post.get("title") or "Untitled"
                                content = post.get("post_text") or ""
                                if not content:
                                    site_errors.append("Post content is empty")
                                    continue

                                wp_client = WordPressClient(
                                    site_url=creds["site_url"],
                                    username=creds["username"],
                                    app_password=creds["app_password"],
                                )
                                wp_post = await wp_client.create_post(
                                    title=title,
                                    content=content,
                                    status="publish",
                                )
                                last_link = wp_post.get("link", "") or last_link
                                ok_any = True
                                logger.info(
                                    "Published post %s to WordPress site=%s "
                                    "(wp_post_id=%s, user_id=%s)",
                                    post["id"],
                                    site_url,
                                    wp_post.get("id"),
                                    uid,
                                )
                                await bump_channel_counter(
                                    uid,
                                    channel_id=channel_id,
                                    network="wp",
                                    external_id=site_url,
                                    sent=1,
                                    direction="published",
                                    platform="wp",
                                    post_id=int(post["id"]),
                                    metadata={"url": last_link},
                                )

                            if ok_any:
                                await cur.execute(
                                    """
                                    UPDATE wp_posts
                                    SET status = 'published',
                                        url = %s,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = %s
                                    """,
                                    (last_link, post["id"]),
                                )
                                published_count += 1
                            else:
                                err = "; ".join(site_errors) or "Publish failed"
                                await self._update_post_status(
                                    cur, post["id"], "failed", err
                                )
                                failed_count += 1
                                errors.append(
                                    {
                                        "post_id": post["id"],
                                        "user_id": uid,
                                        "error": err,
                                    }
                                )
                        except Exception as exc:
                            error_msg = str(exc)
                            logger.error(
                                "Failed to publish post %s (user_id=%s): %s",
                                post["id"],
                                uid,
                                error_msg,
                            )
                            await self._update_post_status(
                                cur, post["id"], "failed", error_msg
                            )
                            errors.append(
                                {
                                    "post_id": post["id"],
                                    "user_id": uid,
                                    "error": error_msg,
                                }
                            )
                            failed_count += 1

                await conn.commit()
                return {
                    "published": published_count,
                    "failed": failed_count,
                    "errors": errors,
                }
        finally:
            await release_db_connection(conn)

    async def _resolve_sites_for_post(
        self,
        user_id: int,
        post: Dict[str, Any],
        publish_channels: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prefer post.target_channels; else own publish-enabled WP channels; else profile."""
        explicit = post_target_sites(post)
        result: List[Dict[str, Any]] = []

        if explicit:
            for site in explicit:
                # Only treat as WP site URL (http/https or matching a WP channel).
                matched = next(
                    (
                        c
                        for c in publish_channels
                        if site_urls_match(str(c.get("external_id") or ""), site)
                    ),
                    None,
                )
                if matched:
                    result.append(
                        {
                            "site_url": str(matched.get("external_id") or site),
                            "channel_id": matched.get("id"),
                        }
                    )
                    continue
                if site.lower().startswith(("http://", "https://")) or "." in site:
                    result.append({"site_url": site, "channel_id": None})
            if result:
                return result

        for ch in publish_channels:
            ext = str(ch.get("external_id") or "").strip()
            if not ext:
                continue
            result.append({"site_url": ext, "channel_id": ch.get("id")})
        if result:
            return result

        # Legacy: single profile site
        profile = await load_wp_publish_profile(user_id)
        if profile and profile.get("site_url"):
            return [
                {
                    "site_url": str(profile["site_url"]),
                    "channel_id": None,
                }
            ]
        return []

    async def _update_post_status(
        self,
        cursor,
        post_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        await cursor.execute(
            """
            UPDATE wp_posts
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (status, post_id),
        )
        if error_message:
            logger.warning("wp_posts id=%s → %s: %s", post_id, status, error_message)


publish_service = PublishService()

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
from shared.bot_internal import claim_ready_posts, mark_post_published
from shared.db.bot_queue import claimed_target_as_post
from shared.db.posts_repo import PostsRepository, PublishResult

logger = logging.getLogger(__name__)


class PublishService:
    """Публикация постов из wp_posts в WordPress по brand channel / target_channels."""

    async def publish_pending_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        claimed = await self._claim_unified_posts(user_id)
        if not claimed:
            claimed = await claim_ready_posts(
            settings.CORE_SERVICE_URL or "",
            platform="wp",
            limit=settings.PUBLISH_POSTS_LIMIT,
            user_id=user_id,
        )
        if not claimed:
            return {"published": 0, "failed": 0, "errors": []}

        published_count = 0
        failed_count = 0
        errors: list[dict[str, Any]] = []

        posts_by_user: Dict[int, List[Dict[str, Any]]] = {}
        for post in claimed:
            uid = int(post["user_id"])
            posts_by_user.setdefault(uid, []).append(post)

        for uid, posts in posts_by_user.items():
            publish_channels = await list_wp_publish_channels(uid)
            for post in posts:
                try:
                    sites = await self._resolve_sites_for_post(uid, post, publish_channels)
                    if not sites:
                        await mark_post_published(
                            settings.CORE_SERVICE_URL or "",
                            platform="wp",
                            post_id=int(post["id"]),
                            error="No WordPress publish target (brand channel or profile)",
                        )
                        await self._record_target_result(
                            post,
                            ok=False,
                            error="No WordPress publish target (brand channel or profile)",
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
                            site_errors.append(f"No credentials for site {site_url}")
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
                        await mark_post_published(
                            settings.CORE_SERVICE_URL or "",
                            platform="wp",
                            post_id=int(post.get("_post_id") or post["id"]),
                            external_id=last_link or None,
                        )
                        await self._record_target_result(
                            post, ok=True, external_id=last_link or None
                        )
                        published_count += 1
                    else:
                        err = "; ".join(site_errors) or "Publish failed"
                        await mark_post_published(
                            settings.CORE_SERVICE_URL or "",
                            platform="wp",
                            post_id=int(post.get("_post_id") or post["id"]),
                            error=err,
                        )
                        await self._record_target_result(post, ok=False, error=err)
                        failed_count += 1
                        errors.append({"post_id": post["id"], "user_id": uid, "error": err})
                except Exception as exc:
                    error_msg = str(exc)
                    logger.error(
                        "Failed to publish post %s (user_id=%s): %s",
                        post["id"],
                        uid,
                        error_msg,
                    )
                    await mark_post_published(
                        settings.CORE_SERVICE_URL or "",
                        platform="wp",
                        post_id=int(post.get("_post_id") or post["id"]),
                        error=error_msg,
                    )
                    await self._record_target_result(post, ok=False, error=error_msg)
                    errors.append(
                        {"post_id": post["id"], "user_id": uid, "error": error_msg}
                    )
                    failed_count += 1

        return {
            "published": published_count,
            "failed": failed_count,
            "errors": errors,
        }

    async def _claim_unified_posts(self, user_id: Optional[int]) -> List[Dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("BEGIN")
                    rows = await PostsRepository(cur).claim_publish(
                        platform="wp",
                        limit=settings.PUBLISH_POSTS_LIMIT,
                        user_id=user_id,
                    )
                    await cur.execute("COMMIT")
                except Exception:
                    await cur.execute("ROLLBACK")
                    raise
            return [claimed_target_as_post(row) for row in rows]
        except Exception:
            logger.debug("unified wp claim skipped", exc_info=True)
            return []
        finally:
            await release_db_connection(conn)

    async def _record_target_result(
        self,
        post: Dict[str, Any],
        *,
        ok: bool,
        external_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        if post.get("_queue") != "targets":
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                result: Dict[str, Any] = {}
                if external_id:
                    result["remote_id"] = external_id
                if error:
                    result["error"] = error
                await PostsRepository(cur).apply_publish_result(
                    PublishResult(target_id=int(post["_target_id"]), ok=ok, result=result)
                )
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

        profile = await load_wp_publish_profile(user_id)
        if profile and profile.get("site_url"):
            return [
                {
                    "site_url": str(profile["site_url"]),
                    "channel_id": None,
                }
            ]
        return []


publish_service = PublishService()

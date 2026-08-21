"""Сервис для сбора постов из WordPress."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from config import settings
from database import get_db_connection, release_db_connection
from services.wordpress_client import WordPressClient

logger = logging.getLogger(__name__)


class CollectService:
    """Сбор постов из WordPress в wp_posts через wp_collect_profile + wp_publish_profile."""

    async def collect_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                query = """
                    SELECT
                        cp.user_id,
                        cp.collect_limit,
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
                collected_count = 0
                failed_count = 0
                errors: list[dict[str, Any]] = []
                limit_per_pass = settings.COLLECT_POSTS_LIMIT

                for row in rows:
                    if collected_count >= limit_per_pass:
                        break

                    record = dict(zip(columns, row))
                    uid = record["user_id"]
                    site_url = record.get("site_url")
                    username = record.get("username")
                    app_password = record.get("app_password")

                    if not site_url or not username or not app_password:
                        errors.append({
                            "user_id": uid,
                            "error": "Incomplete WordPress collect credentials or site_url",
                        })
                        failed_count += 1
                        continue

                    try:
                        wp_client = WordPressClient(
                            site_url=site_url,
                            username=username,
                            app_password=app_password,
                        )

                        page = 1
                        per_page = 20
                        total_collected_for_user = 0

                        while collected_count < limit_per_pass:
                            result = await wp_client.get_posts(
                                per_page=per_page,
                                page=page,
                                status="publish",
                            )
                            posts = result.get("posts", [])
                            if not posts:
                                break

                            for wp_post in posts:
                                if collected_count >= limit_per_pass:
                                    break

                                wp_post_link = wp_post.get("link", "")
                                await cur.execute(
                                    """
                                    SELECT id FROM wp_posts
                                    WHERE user_id = %s AND url = %s
                                    """,
                                    (uid, wp_post_link),
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
                                author_name = None
                                if wp_post.get("_embedded") and wp_post["_embedded"].get("author"):
                                    author_name = wp_post["_embedded"]["author"][0].get("name")

                                await cur.execute(
                                    """
                                    INSERT INTO wp_posts (
                                        user_id, domain, url, title, author,
                                        post_date, post_text, status, post_type,
                                        to_wp, created_at, updated_at
                                    ) VALUES (
                                        %s, %s, %s, %s, %s,
                                        %s, %s, %s, %s,
                                        TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                                    )
                                    """,
                                    (
                                        uid,
                                        site_url,
                                        wp_post_link,
                                        title,
                                        author_name,
                                        post_date,
                                        content,
                                        "collected",
                                        "wp",
                                    ),
                                )
                                total_collected_for_user += 1
                                collected_count += 1

                            total_pages = result.get("total_pages", 0)
                            if page >= total_pages:
                                break
                            page += 1

                        if total_collected_for_user > 0:
                            logger.info(
                                "Collected %d posts from WordPress for user_id=%s",
                                total_collected_for_user,
                                uid,
                            )
                    except Exception as exc:
                        error_msg = f"Error processing user_id={uid}: {exc!s}"
                        logger.error(error_msg)
                        errors.append({"user_id": uid, "error": error_msg})
                        failed_count += 1

                await conn.commit()
                return {
                    "collected": collected_count,
                    "failed": failed_count,
                    "errors": errors,
                }
        finally:
            await release_db_connection(conn)


collect_service = CollectService()

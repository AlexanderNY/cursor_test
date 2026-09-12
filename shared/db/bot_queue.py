"""Helpers for bot collectors/publishers on the unified posts queue."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from shared.db.posts_repo import (
    PostsRepository,
    PublishResult,
    resolve_publish_platforms,
)


def dest_flags_to_platforms(dest: Mapping[str, Any]) -> list[str]:
    return resolve_publish_platforms(legacy_flags=dest, source_platform=None)


def claimed_target_as_post(row: Mapping[str, Any]) -> dict[str, Any]:
    """Shape a post_targets claim like a legacy *_posts row (id = target id)."""
    post = dict(row)
    target_id = int(row["target_id"])
    post["id"] = target_id
    post["_queue"] = "targets"
    post["_target_id"] = target_id
    post["_post_id"] = int(row["post_id"])
    return post


async def finish_claimed_publish(
    cur: Any,
    post: Mapping[str, Any],
    *,
    ok: bool,
    result: Optional[Mapping[str, Any]] = None,
    status: Optional[str] = None,
) -> bool:
    """Write publish-result for a unified claim. Returns False if post is legacy."""
    if post.get("_queue") != "targets":
        return False
    await PostsRepository(cur).apply_publish_result(
        PublishResult(
            target_id=int(post["_target_id"]),
            ok=ok,
            result=dict(result or {}),
            status=status,
        )
    )
    return True

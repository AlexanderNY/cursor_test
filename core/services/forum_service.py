"""Ветки форума: Workspace и общие обсуждения платформы."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException

from database import get_db_connection, release_db_connection
from schemas import (
    ForumAvatarResponse,
    ForumListResponse,
    ForumPost,
    ForumPostCreate,
    ForumPostUpdate,
    ForumThread,
    ForumThreadCreate,
    ForumThreadDetail,
    ForumThreadUpdate,
    ForumUnreadResponse,
    ForumVoteResponse,
)
from services.forum_policy import (
    ATTACHMENT_KIND_ONLY,
    AVATAR_MAX_BYTES,
    EDIT_EXPIRED,
    EMPTY_TEXT,
    FORBIDDEN,
    NO_WORKSPACE,
    PIN_SCOPE_ONLY,
    POST_NOT_FOUND,
    QUOTE_NOT_IN_THREAD,
    STATUS_KIND_ONLY,
    THREAD_CLOSED,
    THREAD_NOT_FOUND,
    UNKNOWN_STATUS,
    VOTE_KIND_ONLY,
    attachment_public_path,
    attachment_storage_key,
    avatar_public_path,
    avatar_storage_key,
    can_attach,
    can_delete_post,
    can_edit_post,
    can_moderate,
    can_open_thread,
    can_pin,
    can_read_thread,
    can_set_status,
    clean_body,
    clean_title,
    extract_mentions,
    parse_status,
    post_from_row,
    quote_excerpt,
    reply_notice,
    search_pattern,
    sniff_image_type,
    thread_from_row,
    thread_href,
    thread_permissions,
    votes_allowed,
)
from services.roadmap_helpers import next_voted_state
from services.team_access import get_active_group_id, role_in_group
from shared import async_fs
from storage_client import get_storage

logger = logging.getLogger(__name__)

_AVATAR_DIR = Path("uploads/avatars")
_ATTACHMENT_DIR = Path("uploads/forum-attachments")
_VIEWER_SLOTS = 7

_UNREAD_SQL = """
EXISTS(
    SELECT 1 FROM forum_posts op
    WHERE op.thread_id = t.id
      AND op.author_id <> %s
      AND (
        t.author_id = %s
        OR EXISTS (
            SELECT 1 FROM forum_posts mine
            WHERE mine.thread_id = t.id AND mine.author_id = %s
        )
      )
      AND op.created_at > COALESCE(
        (SELECT r.last_read_at FROM forum_reads r
         WHERE r.user_id = %s AND r.thread_id = t.id),
        CASE
            WHEN t.author_id = %s THEN t.created_at
            ELSE COALESCE(
                (SELECT MAX(mp.created_at) FROM forum_posts mp
                 WHERE mp.thread_id = t.id AND mp.author_id = %s),
                t.created_at
            )
        END
      )
)
"""


def _viewer(user_id: int) -> tuple[int, ...]:
    return (user_id,) * _VIEWER_SLOTS


_THREAD_SQL = f"""
SELECT
    t.id,
    t.scope,
    t.group_id,
    g.name,
    t.kind,
    t.title,
    t.body,
    t.author_id,
    COALESCE(NULLIF(u.username, ''), 'участник') AS author_name,
    t.is_closed,
    COALESCE((
        SELECT COUNT(*)::int FROM forum_votes v WHERE v.thread_id = t.id
    ), 0) AS vote_count,
    EXISTS(
        SELECT 1 FROM forum_votes uv
        WHERE uv.thread_id = t.id AND uv.user_id = %s
    ) AS voted,
    COALESCE((
        SELECT COUNT(*)::int FROM forum_posts p WHERE p.thread_id = t.id
    ), 0) AS reply_count,
    t.created_at,
    t.updated_at,
    NULLIF(u.avatar_url, '') AS author_avatar,
    COALESCE(NULLIF(t.status, ''), 'new') AS status,
    COALESCE(t.is_pinned, FALSE) AS is_pinned,
    NULLIF(t.attachment_path, '') AS attachment_path,
    {_UNREAD_SQL} AS unread
FROM forum_threads t
LEFT JOIN users u ON u.id = t.author_id
LEFT JOIN groups g ON g.id = t.group_id
"""


class ForumService:
    """Список, ветки, ответы и голоса за идеи."""

    async def list_threads(
        self,
        user_id: int,
        *,
        scope: str,
        kind: Optional[str],
        query: Optional[str],
        is_platform_admin: bool,
    ) -> ForumListResponse:
        group_id: Optional[int] = None
        group_name: Optional[str] = None
        workspace_role: Optional[str] = None
        if scope == "workspace":
            group_id = await get_active_group_id(user_id)
            if group_id is None:
                return ForumListResponse(
                    scope="workspace",
                    group_id=None,
                    group_name=None,
                    threads=[],
                )
            workspace_role = await role_in_group(user_id, group_id)
            group_name = await self._group_name(group_id)

        kind_param = kind or ""
        pattern = search_pattern(query)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    {_THREAD_SQL}
                    WHERE t.scope = %s
                      AND (%s = 'platform' OR t.group_id = %s)
                      AND (%s = '' OR t.kind = %s)
                      AND (
                        %s = ''
                        OR t.title ILIKE %s ESCAPE '\\'
                        OR t.body ILIKE %s ESCAPE '\\'
                        OR EXISTS (
                            SELECT 1 FROM forum_posts sp
                            WHERE sp.thread_id = t.id
                              AND sp.body ILIKE %s ESCAPE '\\'
                        )
                      )
                    ORDER BY
                        t.is_pinned DESC,
                        CASE WHEN %s = 'suggestion'
                            THEN COALESCE((
                                SELECT COUNT(*)::int FROM forum_votes v2
                                WHERE v2.thread_id = t.id
                            ), 0)
                            ELSE 0
                        END DESC,
                        t.updated_at DESC,
                        t.id DESC
                    LIMIT 80
                    """,
                    (
                        *_viewer(user_id),
                        scope,
                        scope,
                        group_id or 0,
                        kind_param,
                        kind_param,
                        pattern,
                        pattern,
                        pattern,
                        pattern,
                        kind_param,
                    ),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        threads = [
            self._map_thread(
                row,
                user_id=user_id,
                is_platform_admin=is_platform_admin,
                workspace_role=workspace_role,
            )
            for row in rows
        ]
        return ForumListResponse(
            scope=scope,  # type: ignore[arg-type]
            group_id=group_id,
            group_name=group_name,
            threads=threads,
        )

    async def get_thread(
        self,
        user_id: int,
        thread_id: int,
        *,
        is_platform_admin: bool,
    ) -> ForumThreadDetail:
        row = await self._fetch_thread_row(user_id, thread_id)
        if row is None:
            raise HTTPException(status_code=404, detail=THREAD_NOT_FOUND)
        data = thread_from_row(row)
        workspace_role = await self._role_for_scope(
            user_id,
            scope=data["scope"],
            group_id=data["group_id"],
        )
        self._ensure_can_read(data, workspace_role=workspace_role)
        await self._mark_read(user_id, thread_id)
        thread = self._map_thread(
            row,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=workspace_role,
        )
        thread = thread.model_copy(update={"unread": False})
        posts = await self._load_posts(
            thread_id,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=workspace_role if data["scope"] == "workspace" else None,
            is_closed=bool(data["is_closed"]),
        )
        return ForumThreadDetail(**thread.model_dump(), posts=posts)

    async def create_thread(
        self,
        user_id: int,
        payload: ForumThreadCreate,
        *,
        is_platform_admin: bool,
    ) -> ForumThreadDetail:
        title = clean_title(payload.title)
        body = clean_body(payload.body)
        if not title or not body:
            raise HTTPException(status_code=400, detail=EMPTY_TEXT)

        group_id: Optional[int] = None
        workspace_role: Optional[str] = None
        if payload.scope == "workspace":
            group_id = await get_active_group_id(user_id)
            workspace_role = (
                await role_in_group(user_id, group_id) if group_id is not None else None
            )
            if not can_open_thread(scope="workspace", workspace_role=workspace_role):
                raise HTTPException(status_code=400, detail=NO_WORKSPACE)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO forum_threads (
                        scope, group_id, kind, title, body, author_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (payload.scope, group_id, payload.kind, title, body, user_id),
                )
                created = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create thread")
        return await self.get_thread(
            user_id,
            int(created[0]),
            is_platform_admin=is_platform_admin,
        )

    async def add_post(
        self,
        user_id: int,
        thread_id: int,
        payload: ForumPostCreate,
        *,
        is_platform_admin: bool,
    ) -> ForumPost:
        body = clean_body(payload.body)
        if not body:
            raise HTTPException(status_code=400, detail=EMPTY_TEXT)
        loaded = await self._require_readable(user_id, thread_id)
        if loaded["is_closed"]:
            raise HTTPException(status_code=400, detail=THREAD_CLOSED)
        quote_author, quote_body = await self._quote_fields(
            thread_id,
            payload.quote_post_id,
        )

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO forum_posts (
                        thread_id, author_id, body, quote_author, quote_body
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (thread_id, user_id, body, quote_author, quote_body),
                )
                created = await cur.fetchone()
                await cur.execute(
                    """
                    UPDATE forum_threads
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (thread_id,),
                )
                await cur.execute(
                    """
                    SELECT COALESCE(NULLIF(username, ''), 'участник')
                    FROM users WHERE id = %s
                    """,
                    (user_id,),
                )
                name_row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create post")
        author_name = str(name_row[0]) if name_row else "участник"
        await self._notify_reply(
            thread_id=thread_id,
            actor_id=user_id,
            author_name=author_name,
            title=str(loaded["title"]),
            scope=str(loaded["scope"]),
            group_id=loaded["group_id"],
            body=body,
            participants_only=False,
        )
        posts = await self._load_posts(
            thread_id,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
            is_closed=False,
            post_id=int(created[0]),
        )
        if not posts:
            raise HTTPException(status_code=500, detail="Failed to create post")
        return posts[0]

    async def update_thread(
        self,
        user_id: int,
        thread_id: int,
        payload: ForumThreadUpdate,
        *,
        is_platform_admin: bool,
    ) -> ForumThreadDetail:
        loaded = await self._require_readable(user_id, thread_id)
        fields = payload.model_fields_set
        assignments: list[str] = []
        params: list[Any] = []

        if "is_closed" in fields and payload.is_closed is not None:
            if not can_moderate(
                author_id=int(loaded["author_id"]),
                user_id=user_id,
                is_platform_admin=is_platform_admin,
                workspace_role=loaded["workspace_role"],
            ):
                raise HTTPException(status_code=403, detail=FORBIDDEN)
            assignments.append("is_closed = %s")
            params.append(payload.is_closed)
            assignments.append("updated_at = CURRENT_TIMESTAMP")

        if "status" in fields and payload.status is not None:
            if str(loaded["kind"]) != "suggestion":
                raise HTTPException(status_code=400, detail=STATUS_KIND_ONLY)
            if not can_set_status(kind="suggestion", is_platform_admin=is_platform_admin):
                raise HTTPException(status_code=403, detail=FORBIDDEN)
            status = parse_status(payload.status)
            if status is None:
                raise HTTPException(status_code=400, detail=UNKNOWN_STATUS)
            assignments.append("status = %s")
            params.append(status)

        if "is_pinned" in fields and payload.is_pinned is not None:
            if str(loaded["scope"]) != "workspace":
                raise HTTPException(status_code=400, detail=PIN_SCOPE_ONLY)
            if not can_pin(
                scope="workspace",
                workspace_role=loaded["workspace_role"],
            ):
                raise HTTPException(status_code=403, detail=FORBIDDEN)
            if payload.is_pinned and loaded["group_id"] is not None:
                await self._unpin_others(int(loaded["group_id"]), thread_id)
            assignments.append("is_pinned = %s")
            params.append(payload.is_pinned)

        if assignments:
            params.append(thread_id)
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"UPDATE forum_threads SET {', '.join(assignments)} WHERE id = %s",
                        tuple(params),
                    )
            finally:
                await release_db_connection(conn)
        return await self.get_thread(
            user_id,
            thread_id,
            is_platform_admin=is_platform_admin,
        )

    async def delete_thread(
        self,
        user_id: int,
        thread_id: int,
        *,
        is_platform_admin: bool,
    ) -> dict[str, Any]:
        loaded = await self._require_readable(user_id, thread_id)
        if not can_moderate(
            author_id=int(loaded["author_id"]),
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
        ):
            raise HTTPException(status_code=403, detail=FORBIDDEN)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM forum_threads WHERE id = %s RETURNING id",
                    (thread_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail=THREAD_NOT_FOUND)
        return {"message": "Thread deleted", "id": thread_id}

    async def delete_post(
        self,
        user_id: int,
        post_id: int,
        *,
        is_platform_admin: bool,
    ) -> dict[str, Any]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.thread_id, p.author_id
                    FROM forum_posts p
                    WHERE p.id = %s
                    """,
                    (post_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail=POST_NOT_FOUND)
        thread_id = int(row[1])
        loaded = await self._require_readable(user_id, thread_id)
        if not can_delete_post(
            post_author_id=int(row[2]),
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
        ):
            raise HTTPException(status_code=403, detail=FORBIDDEN)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM forum_posts WHERE id = %s",
                    (post_id,),
                )
        finally:
            await release_db_connection(conn)
        return {"message": "Post deleted", "id": post_id, "thread_id": thread_id}

    async def toggle_vote(
        self,
        user_id: int,
        thread_id: int,
    ) -> ForumVoteResponse:
        loaded = await self._require_readable(user_id, thread_id)
        if not votes_allowed(str(loaded["kind"])):
            raise HTTPException(status_code=400, detail=VOTE_KIND_ONLY)
        if loaded["is_closed"]:
            raise HTTPException(status_code=400, detail=THREAD_CLOSED)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id FROM forum_votes
                    WHERE thread_id = %s AND user_id = %s
                    """,
                    (thread_id, user_id),
                )
                existing = await cur.fetchone()
                will_vote = next_voted_state(already_voted=existing is not None)
                if will_vote:
                    await cur.execute(
                        """
                        INSERT INTO forum_votes (thread_id, user_id)
                        VALUES (%s, %s)
                        ON CONFLICT (thread_id, user_id) DO NOTHING
                        """,
                        (thread_id, user_id),
                    )
                else:
                    await cur.execute(
                        """
                        DELETE FROM forum_votes
                        WHERE thread_id = %s AND user_id = %s
                        """,
                        (thread_id, user_id),
                    )
                await cur.execute(
                    "SELECT COUNT(*)::int FROM forum_votes WHERE thread_id = %s",
                    (thread_id,),
                )
                count_row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        stored = int(count_row[0] if count_row else 0)
        if stored < 0:
            stored = 0
        return ForumVoteResponse(
            thread_id=thread_id,
            voted=will_vote,
            vote_count=stored,
        )

    async def _group_name(self, group_id: int) -> Optional[str]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT name FROM groups WHERE id = %s", (group_id,))
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row or row[0] is None:
            return None
        return str(row[0])

    async def _fetch_thread_row(
        self,
        user_id: int,
        thread_id: int,
    ) -> Optional[tuple[Any, ...]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"{_THREAD_SQL} WHERE t.id = %s",
                    (*_viewer(user_id), thread_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        return row

    async def _role_for_scope(
        self,
        user_id: int,
        *,
        scope: str,
        group_id: Optional[int],
    ) -> Optional[str]:
        if scope != "workspace" or group_id is None:
            return None
        return await role_in_group(user_id, group_id)

    def _ensure_can_read(
        self,
        data: dict[str, Any],
        *,
        workspace_role: Optional[str],
    ) -> None:
        is_member = workspace_role is not None
        if can_read_thread(
            scope=str(data["scope"]),
            group_id=data["group_id"],
            is_member=is_member,
        ):
            return
        raise HTTPException(status_code=404, detail=THREAD_NOT_FOUND)

    async def _require_readable(
        self,
        user_id: int,
        thread_id: int,
    ) -> dict[str, Any]:
        row = await self._fetch_thread_row(user_id, thread_id)
        if row is None:
            raise HTTPException(status_code=404, detail=THREAD_NOT_FOUND)
        data = thread_from_row(row)
        workspace_role = await self._role_for_scope(
            user_id,
            scope=data["scope"],
            group_id=data["group_id"],
        )
        self._ensure_can_read(data, workspace_role=workspace_role)
        data["workspace_role"] = (
            workspace_role if data["scope"] == "workspace" else None
        )
        return data

    async def _load_posts(
        self,
        thread_id: int,
        *,
        user_id: int,
        is_platform_admin: bool,
        workspace_role: Optional[str],
        is_closed: bool,
        post_id: Optional[int] = None,
    ) -> list[ForumPost]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        p.id,
                        p.thread_id,
                        p.body,
                        p.author_id,
                        COALESCE(NULLIF(u.username, ''), 'участник'),
                        p.created_at,
                        NULLIF(u.avatar_url, ''),
                        p.updated_at,
                        NULLIF(p.quote_author, ''),
                        NULLIF(p.quote_body, '')
                    FROM forum_posts p
                    LEFT JOIN users u ON u.id = p.author_id
                    WHERE p.thread_id = %s
                      AND (%s::int IS NULL OR p.id = %s)
                    ORDER BY p.created_at ASC, p.id ASC
                    LIMIT 300
                    """,
                    (thread_id, post_id, post_id),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        now = datetime.now(timezone.utc)
        posts: list[ForumPost] = []
        for row in rows:
            item = post_from_row(row)
            item["can_delete"] = can_delete_post(
                post_author_id=item["author_id"],
                user_id=user_id,
                is_platform_admin=is_platform_admin,
                workspace_role=workspace_role,
            )
            item["can_edit"] = can_edit_post(
                post_author_id=item["author_id"],
                user_id=user_id,
                created_at=item["created_at"],
                now=now,
                is_closed=is_closed,
            )
            posts.append(ForumPost(**item))
        return posts

    def _map_thread(
        self,
        row: tuple[Any, ...],
        *,
        user_id: int,
        is_platform_admin: bool,
        workspace_role: Optional[str],
    ) -> ForumThread:
        data = thread_from_row(row)
        role = workspace_role if data["scope"] == "workspace" else None
        flags = thread_permissions(
            author_id=data["author_id"],
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=role,
            is_closed=data["is_closed"],
            kind=data["kind"],
            scope=data["scope"],
        )
        return ForumThread(**data, **flags)

    async def edit_post(
        self,
        user_id: int,
        post_id: int,
        payload: ForumPostUpdate,
        *,
        is_platform_admin: bool,
    ) -> ForumPost:
        body = clean_body(payload.body)
        if not body:
            raise HTTPException(status_code=400, detail=EMPTY_TEXT)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.thread_id, p.author_id, p.created_at
                    FROM forum_posts p
                    WHERE p.id = %s
                    """,
                    (post_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail=POST_NOT_FOUND)
        thread_id = int(row[1])
        loaded = await self._require_readable(user_id, thread_id)
        if not can_edit_post(
            post_author_id=int(row[2]),
            user_id=user_id,
            created_at=row[3],
            now=datetime.now(timezone.utc),
            is_closed=bool(loaded["is_closed"]),
        ):
            raise HTTPException(status_code=403, detail=EDIT_EXPIRED)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE forum_posts
                    SET body = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (body, post_id),
                )
                await cur.execute(
                    """
                    SELECT COALESCE(NULLIF(username, ''), 'участник')
                    FROM users WHERE id = %s
                    """,
                    (user_id,),
                )
                name_row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        author_name = str(name_row[0]) if name_row else "участник"
        await self._notify_reply(
            thread_id=thread_id,
            actor_id=user_id,
            author_name=author_name,
            title=str(loaded["title"]),
            scope=str(loaded["scope"]),
            group_id=loaded["group_id"],
            body=body,
            participants_only=True,
        )
        posts = await self._load_posts(
            thread_id,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
            is_closed=bool(loaded["is_closed"]),
            post_id=post_id,
        )
        if not posts:
            raise HTTPException(status_code=404, detail=POST_NOT_FOUND)
        return posts[0]

    async def unread_count(self, user_id: int) -> ForumUnreadResponse:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT COUNT(*)::int
                    FROM forum_threads t
                    WHERE {_UNREAD_SQL}
                      AND (
                        t.scope = 'platform'
                        OR EXISTS (
                            SELECT 1 FROM group_members gm
                            WHERE gm.group_id = t.group_id AND gm.user_id = %s
                        )
                      )
                    """,
                    (*_viewer(user_id)[1:], user_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        return ForumUnreadResponse(count=int(row[0] if row else 0))

    async def save_attachment(
        self,
        user_id: int,
        thread_id: int,
        content: bytes,
        *,
        is_platform_admin: bool,
    ) -> ForumThreadDetail:
        if len(content) > AVATAR_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Файл больше 2 МБ")
        content_type = sniff_image_type(content)
        if content_type is None:
            raise HTTPException(
                status_code=400,
                detail="Нужен файл JPEG, PNG, WEBP или GIF",
            )
        loaded = await self._require_readable(user_id, thread_id)
        moderate = can_moderate(
            author_id=int(loaded["author_id"]),
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
        )
        if str(loaded["kind"]) != "bug_report":
            raise HTTPException(status_code=400, detail=ATTACHMENT_KIND_ONLY)
        if not can_attach(
            kind="bug_report",
            is_closed=bool(loaded["is_closed"]),
            can_moderate_thread=moderate,
        ):
            raise HTTPException(status_code=403, detail=FORBIDDEN)
        key = attachment_storage_key(thread_id)
        storage = get_storage()
        if storage:
            await storage.put(key, content, content_type=content_type)
        else:
            await async_fs.makedirs(_ATTACHMENT_DIR)
            await async_fs.write_bytes(_ATTACHMENT_DIR / str(thread_id), content)
        public_path = attachment_public_path(thread_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE forum_threads SET attachment_path = %s WHERE id = %s",
                    (public_path, thread_id),
                )
        finally:
            await release_db_connection(conn)
        return await self.get_thread(
            user_id,
            thread_id,
            is_platform_admin=is_platform_admin,
        )

    async def read_attachment(self, thread_id: int) -> tuple[bytes, str]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT NULLIF(attachment_path, '') FROM forum_threads WHERE id = %s",
                    (thread_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Файл не найден")
        key = attachment_storage_key(thread_id)
        data: bytes | None = None
        storage = get_storage()
        if storage:
            data = await storage.get_bytes(key)
        if not data:
            path = _ATTACHMENT_DIR / str(thread_id)
            if path.is_file():
                data = await async_fs.read_bytes(path)
        if not data:
            raise HTTPException(status_code=404, detail="Файл не найден")
        content_type = sniff_image_type(data)
        if content_type is None:
            raise HTTPException(status_code=404, detail="Файл не найден")
        return data, content_type

    async def _mark_read(self, user_id: int, thread_id: int) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO forum_reads (user_id, thread_id, last_read_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, thread_id)
                    DO UPDATE SET last_read_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, thread_id),
                )
        finally:
            await release_db_connection(conn)

    async def _unpin_others(self, group_id: int, thread_id: int) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE forum_threads
                    SET is_pinned = FALSE
                    WHERE group_id = %s AND id <> %s AND is_pinned IS TRUE
                    """,
                    (group_id, thread_id),
                )
        finally:
            await release_db_connection(conn)

    async def _quote_fields(
        self,
        thread_id: int,
        quote_post_id: Optional[int],
    ) -> tuple[Optional[str], Optional[str]]:
        if quote_post_id is None:
            return None, None
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.body, COALESCE(NULLIF(u.username, ''), 'участник')
                    FROM forum_posts p
                    LEFT JOIN users u ON u.id = p.author_id
                    WHERE p.id = %s AND p.thread_id = %s
                    """,
                    (quote_post_id, thread_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=400, detail=QUOTE_NOT_IN_THREAD)
        excerpt = quote_excerpt(str(row[0]))
        if not excerpt:
            return None, None
        return str(row[1]), excerpt

    async def _notify_reply(
        self,
        *,
        thread_id: int,
        actor_id: int,
        author_name: str,
        title: str,
        scope: str,
        group_id: Optional[int],
        body: str,
        participants_only: bool,
    ) -> None:
        """Оповещение участникам ветки и упомянутым. Ошибка записи не отменяет ответ."""
        try:
            names = extract_mentions(body)
            mentioned = await self._mention_user_ids(names, group_id=group_id, scope=scope)
            recipients = set(mentioned)
            if not participants_only:
                recipients.update(await self._participant_ids(thread_id))
            recipients.discard(actor_id)
            recipients.discard(0)
            if not recipients:
                return
            href = thread_href(scope=scope, thread_id=thread_id)
            marker = f"thread={thread_id}\""
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    for recipient_id in list(recipients)[:30]:
                        message = reply_notice(
                            author_name=author_name,
                            title=title,
                            href=href,
                            mentioned=recipient_id in mentioned,
                        )
                        await cur.execute(
                            """
                            DELETE FROM notifications
                            WHERE user_id = %s
                              AND type = 'forum_reply'
                              AND message LIKE %s
                            """,
                            (recipient_id, f"%{marker}%"),
                        )
                        await cur.execute(
                            """
                            INSERT INTO notifications (message, user_id, type)
                            VALUES (%s, %s, 'forum_reply')
                            """,
                            (message, recipient_id),
                        )
            finally:
                await release_db_connection(conn)
        except Exception:
            logger.exception("forum reply notification failed")

    async def _participant_ids(self, thread_id: int) -> set[int]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT author_id FROM forum_threads WHERE id = %s
                    UNION
                    SELECT author_id FROM forum_posts WHERE thread_id = %s
                    """,
                    (thread_id, thread_id),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        return {int(row[0]) for row in rows if row and row[0]}

    async def _mention_user_ids(
        self,
        names: list[str],
        *,
        group_id: Optional[int],
        scope: str,
    ) -> set[int]:
        if not names:
            return set()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if scope == "workspace" and group_id is not None:
                    await cur.execute(
                        """
                        SELECT u.id
                        FROM users u
                        JOIN group_members gm ON gm.user_id = u.id AND gm.group_id = %s
                        WHERE lower(u.username) = ANY(%s)
                        """,
                        (group_id, names),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id FROM users
                        WHERE lower(username) = ANY(%s)
                        """,
                        (names,),
                    )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        return {int(row[0]) for row in rows}

    async def save_avatar(self, user_id: int, content: bytes) -> ForumAvatarResponse:
        if len(content) > AVATAR_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Фото больше 2 МБ")
        content_type = sniff_image_type(content)
        if content_type is None:
            raise HTTPException(
                status_code=400,
                detail="Нужен файл JPEG, PNG, WEBP или GIF",
            )
        key = avatar_storage_key(user_id)
        storage = get_storage()
        if storage:
            await storage.put(key, content, content_type=content_type)
        else:
            await async_fs.makedirs(_AVATAR_DIR)
            await async_fs.write_bytes(_AVATAR_DIR / str(user_id), content)
        public_path = avatar_public_path(user_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET avatar_url = %s WHERE id = %s RETURNING id",
                    (public_path, user_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return ForumAvatarResponse(avatar_url=public_path)

    async def delete_avatar(self, user_id: int) -> ForumAvatarResponse:
        storage = get_storage()
        if storage:
            try:
                await storage.delete_object(avatar_storage_key(user_id))
            except Exception:
                logger.exception("avatar object delete failed")
        await async_fs.unlink_quiet(_AVATAR_DIR / str(user_id))
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET avatar_url = NULL WHERE id = %s RETURNING id",
                    (user_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return ForumAvatarResponse(avatar_url="")

    async def read_avatar(self, user_id: int) -> tuple[bytes, str]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT NULLIF(avatar_url, '') FROM users WHERE id = %s",
                    (user_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        key = avatar_storage_key(user_id)
        data: bytes | None = None
        storage = get_storage()
        if storage:
            data = await storage.get_bytes(key)
        if not data:
            path = _AVATAR_DIR / str(user_id)
            if path.is_file():
                data = await async_fs.read_bytes(path)
        if not data:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        content_type = sniff_image_type(data)
        if content_type is None:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        return data, content_type


forum_service = ForumService()

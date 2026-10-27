"""Ветки форума: Workspace и общие обсуждения платформы."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from database import get_db_connection, release_db_connection
from schemas import (
    ForumListResponse,
    ForumPost,
    ForumPostCreate,
    ForumThread,
    ForumThreadCreate,
    ForumThreadDetail,
    ForumThreadUpdate,
    ForumVoteResponse,
)
from services.forum_policy import (
    EMPTY_TEXT,
    FORBIDDEN,
    NO_WORKSPACE,
    POST_NOT_FOUND,
    THREAD_CLOSED,
    THREAD_NOT_FOUND,
    VOTE_KIND_ONLY,
    can_delete_post,
    can_moderate,
    can_open_thread,
    can_read_thread,
    clean_body,
    clean_title,
    post_from_row,
    thread_from_row,
    thread_permissions,
    votes_allowed,
)
from services.roadmap_helpers import next_voted_state
from services.team_access import get_active_group_id, role_in_group


_THREAD_SQL = """
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
    t.updated_at
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
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    {_THREAD_SQL}
                    WHERE t.scope = %s
                      AND (%s = 'platform' OR t.group_id = %s)
                      AND (%s = '' OR t.kind = %s)
                    ORDER BY
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
                        user_id,
                        scope,
                        scope,
                        group_id or 0,
                        kind_param,
                        kind_param,
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
        thread = self._map_thread(
            row,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=workspace_role,
        )
        posts = await self._load_posts(
            thread_id,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=workspace_role if data["scope"] == "workspace" else None,
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

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO forum_posts (thread_id, author_id, body)
                    VALUES (%s, %s, %s)
                    RETURNING id, thread_id, body, author_id, created_at
                    """,
                    (thread_id, user_id, body),
                )
                row = await cur.fetchone()
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
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create post")
        author_name = name_row[0] if name_row else "участник"
        flags = can_delete_post(
            post_author_id=user_id,
            user_id=user_id,
            is_platform_admin=is_platform_admin,
            workspace_role=loaded["workspace_role"],
        )
        return ForumPost(
            id=row[0],
            thread_id=row[1],
            body=row[2],
            author_id=row[3],
            author_name=str(author_name),
            created_at=row[4],
            can_delete=flags,
        )

    async def set_closed(
        self,
        user_id: int,
        thread_id: int,
        payload: ForumThreadUpdate,
        *,
        is_platform_admin: bool,
    ) -> ForumThreadDetail:
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
                    """
                    UPDATE forum_threads
                    SET is_closed = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (payload.is_closed, thread_id),
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
                    (user_id, thread_id),
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
                        p.created_at
                    FROM forum_posts p
                    LEFT JOIN users u ON u.id = p.author_id
                    WHERE p.thread_id = %s
                    ORDER BY p.created_at ASC, p.id ASC
                    LIMIT 300
                    """,
                    (thread_id,),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        posts: list[ForumPost] = []
        for row in rows:
            item = post_from_row(row)
            item["can_delete"] = can_delete_post(
                post_author_id=item["author_id"],
                user_id=user_id,
                is_platform_admin=is_platform_admin,
                workspace_role=workspace_role,
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
        )
        return ForumThread(**data, **flags)


forum_service = ForumService()

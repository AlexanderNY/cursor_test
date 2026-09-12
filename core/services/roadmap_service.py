"""Сервис голосований roadmap («Что далее»)."""

from typing import Any, Mapping, Optional

from fastapi import HTTPException

from database import get_db_connection, release_db_connection
from schemas import (
    RoadmapItem,
    RoadmapItemCreate,
    RoadmapItemUpdate,
    RoadmapListResponse,
    RoadmapVoteResponse,
)
from services.roadmap_helpers import next_voted_state, row_to_roadmap_dict


class RoadmapService:
    """CRUD пунктов roadmap и toggle голосов."""

    async def list_items(
        self,
        user_id: int,
        *,
        include_inactive: bool = False,
    ) -> RoadmapListResponse:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                active_filter = "" if include_inactive else "WHERE i.is_active = TRUE"
                await cur.execute(
                    f"""
                    SELECT
                        i.id,
                        i.title,
                        i.description,
                        i.is_active,
                        i.created_by,
                        i.created_at,
                        i.updated_at,
                        COALESCE(v.vote_count, 0) AS vote_count,
                        EXISTS(
                            SELECT 1 FROM roadmap_votes uv
                            WHERE uv.item_id = i.id AND uv.user_id = %s
                        ) AS voted
                    FROM roadmap_items i
                    LEFT JOIN (
                        SELECT item_id, COUNT(*)::int AS vote_count
                        FROM roadmap_votes
                        GROUP BY item_id
                    ) v ON v.item_id = i.id
                    {active_filter}
                    ORDER BY vote_count DESC, i.created_at DESC, i.id DESC
                    """,
                    (user_id,),
                )
                rows = await cur.fetchall()
                items = [
                    RoadmapItem(**row_to_roadmap_dict(row[:-1], voted=bool(row[8])))
                    for row in rows
                ]
                return RoadmapListResponse(items=items)
        finally:
            await release_db_connection(conn)

    async def create_item(
        self,
        payload: RoadmapItemCreate,
        created_by: int,
    ) -> RoadmapItem:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")

        description = payload.description.strip() if payload.description else None
        if description == "":
            description = None

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO roadmap_items (title, description, created_by)
                    VALUES (%s, %s, %s)
                    RETURNING id, title, description, is_active, created_by,
                              created_at, updated_at
                    """,
                    (title, description, created_by),
                )
                row = await cur.fetchone()
                if not row:
                    raise HTTPException(status_code=500, detail="Failed to create roadmap item")
                return RoadmapItem(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    is_active=bool(row[3]),
                    created_by=row[4],
                    created_at=row[5],
                    updated_at=row[6],
                    vote_count=0,
                    voted=False,
                )
        finally:
            await release_db_connection(conn)

    async def update_item(
        self,
        item_id: int,
        payload: RoadmapItemUpdate,
    ) -> RoadmapItem:
        updates: dict[str, Any] = {}
        if payload.title is not None:
            title = payload.title.strip()
            if not title:
                raise HTTPException(status_code=400, detail="Title is required")
            updates["title"] = title
        if payload.description is not None:
            description = payload.description.strip()
            updates["description"] = description if description else None
        if payload.is_active is not None:
            updates["is_active"] = payload.is_active

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_parts = [f"{column} = %s" for column in updates]
        set_parts.append("updated_at = CURRENT_TIMESTAMP")
        values = list(updates.values())
        values.append(item_id)

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE roadmap_items
                    SET {", ".join(set_parts)}
                    WHERE id = %s
                    RETURNING id
                    """,
                    values,
                )
                row = await cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Roadmap item not found")
                return await self._get_item_with_counts(cur, item_id, user_id=None)
        finally:
            await release_db_connection(conn)

    async def delete_item(self, item_id: int) -> Mapping[str, Any]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM roadmap_items WHERE id = %s RETURNING id",
                    (item_id,),
                )
                row = await cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Roadmap item not found")
                return {"message": "Roadmap item deleted successfully", "id": item_id}
        finally:
            await release_db_connection(conn)

    async def toggle_vote(self, item_id: int, user_id: int) -> RoadmapVoteResponse:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, is_active FROM roadmap_items WHERE id = %s
                    """,
                    (item_id,),
                )
                item_row = await cur.fetchone()
                if not item_row:
                    raise HTTPException(status_code=404, detail="Roadmap item not found")
                if not item_row[1]:
                    raise HTTPException(status_code=400, detail="Cannot vote on inactive item")

                await cur.execute(
                    """
                    SELECT id FROM roadmap_votes
                    WHERE item_id = %s AND user_id = %s
                    """,
                    (item_id, user_id),
                )
                existing = await cur.fetchone()
                already_voted = existing is not None
                will_vote = next_voted_state(already_voted=already_voted)

                if will_vote:
                    await cur.execute(
                        """
                        INSERT INTO roadmap_votes (item_id, user_id)
                        VALUES (%s, %s)
                        ON CONFLICT (item_id, user_id) DO NOTHING
                        """,
                        (item_id, user_id),
                    )
                else:
                    await cur.execute(
                        """
                        DELETE FROM roadmap_votes
                        WHERE item_id = %s AND user_id = %s
                        """,
                        (item_id, user_id),
                    )

                await cur.execute(
                    """
                    SELECT COUNT(*)::int FROM roadmap_votes WHERE item_id = %s
                    """,
                    (item_id,),
                )
                count_row = await cur.fetchone()
                vote_count = int(count_row[0] if count_row else 0)

                return RoadmapVoteResponse(
                    item_id=item_id,
                    voted=will_vote,
                    vote_count=vote_count,
                )
        finally:
            await release_db_connection(conn)

    async def _get_item_with_counts(
        self,
        cur: Any,
        item_id: int,
        *,
        user_id: Optional[int],
    ) -> RoadmapItem:
        await cur.execute(
            """
            SELECT
                i.id,
                i.title,
                i.description,
                i.is_active,
                i.created_by,
                i.created_at,
                i.updated_at,
                COALESCE((
                    SELECT COUNT(*)::int FROM roadmap_votes rv WHERE rv.item_id = i.id
                ), 0) AS vote_count,
                CASE
                    WHEN %s IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM roadmap_votes uv
                        WHERE uv.item_id = i.id AND uv.user_id = %s
                    )
                END AS voted
            FROM roadmap_items i
            WHERE i.id = %s
            """,
            (user_id, user_id, item_id),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Roadmap item not found")
        return RoadmapItem(**row_to_roadmap_dict(row[:-1], voted=bool(row[8])))


roadmap_service = RoadmapService()

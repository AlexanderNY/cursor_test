"""CRUD метаданных медиатеки опросов."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from database import commit_connection, get_db_connection, release_db_connection, rollback_connection
from services.media_storage import build_public_url, resolve_public_media_url


@dataclass(slots=True)
class MediaAssetRow:
    id: int
    filename: str
    s3_key: str
    original_filename: Optional[str]
    title: str
    description: Optional[str]
    content_type: Optional[str]
    size_bytes: int
    created_at: str


class MediaRepository:
    def _row_from_db(self, r: tuple) -> MediaAssetRow:
        return MediaAssetRow(
            id=int(r[0]),
            filename=str(r[1]),
            s3_key=str(r[2]),
            original_filename=r[3],
            title=str(r[4] or ""),
            description=r[5],
            content_type=r[6],
            size_bytes=int(r[7]),
            created_at=r[8].isoformat() if r[8] else "",
        )

    def to_dict(self, row: MediaAssetRow) -> dict:
        return {
            "id": row.id,
            "filename": row.filename,
            "s3_key": row.s3_key,
            "original_filename": row.original_filename,
            "title": row.title,
            "description": row.description,
            "content_type": row.content_type,
            "size_bytes": row.size_bytes,
            "created_at": row.created_at,
            "public_url": build_public_url(row.filename),
        }

    async def create(
        self,
        *,
        filename: str,
        s3_key: str,
        original_filename: Optional[str],
        title: str,
        description: Optional[str],
        content_type: Optional[str],
        size_bytes: int,
    ) -> MediaAssetRow:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_media_assets (
                        filename, s3_key, original_filename, title, description,
                        content_type, size_bytes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, filename, s3_key, original_filename, title, description,
                              content_type, size_bytes, created_at
                    """,
                    (
                        filename,
                        s3_key,
                        original_filename,
                        title,
                        description,
                        content_type,
                        size_bytes,
                    ),
                )
                row = await cur.fetchone()
                await commit_connection(conn)
                return self._row_from_db(row)
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def list_all(self) -> list[MediaAssetRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, filename, s3_key, original_filename, title, description,
                           content_type, size_bytes, created_at
                    FROM game_media_assets
                    ORDER BY id DESC
                    """
                )
                rows = await cur.fetchall()
                await commit_connection(conn)
                return [self._row_from_db(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def get_by_id(self, asset_id: int) -> Optional[MediaAssetRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, filename, s3_key, original_filename, title, description,
                           content_type, size_bytes, created_at
                    FROM game_media_assets WHERE id = %s
                    """,
                    (asset_id,),
                )
                r = await cur.fetchone()
                await commit_connection(conn)
                return self._row_from_db(r) if r else None
        finally:
            await release_db_connection(conn)

    async def get_by_filename(self, filename: str) -> Optional[MediaAssetRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, filename, s3_key, original_filename, title, description,
                           content_type, size_bytes, created_at
                    FROM game_media_assets WHERE filename = %s
                    """,
                    (filename,),
                )
                r = await cur.fetchone()
                await commit_connection(conn)
                return self._row_from_db(r) if r else None
        finally:
            await release_db_connection(conn)

    async def update(
        self,
        asset_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[MediaAssetRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                fields: list[str] = []
                vals: list[object] = []
                if title is not None:
                    fields.append("title = %s")
                    vals.append(title)
                if description is not None:
                    fields.append("description = %s")
                    vals.append(description)
                if not fields:
                    await commit_connection(conn)
                    return await self.get_by_id(asset_id)
                vals.append(asset_id)
                await cur.execute(
                    f"UPDATE game_media_assets SET {', '.join(fields)} WHERE id = %s",
                    vals,
                )
                await commit_connection(conn)
                return await self.get_by_id(asset_id)
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def delete(self, asset_id: int) -> Optional[str]:
        """Удаляет запись; возвращает s3_key для удаления из S3."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT s3_key FROM game_media_assets WHERE id = %s",
                    (asset_id,),
                )
                r = await cur.fetchone()
                if not r:
                    await commit_connection(conn)
                    return None
                s3_key = str(r[0])
                await cur.execute(
                    "DELETE FROM game_media_assets WHERE id = %s",
                    (asset_id,),
                )
                await commit_connection(conn)
                return s3_key
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)


media_repository = MediaRepository()

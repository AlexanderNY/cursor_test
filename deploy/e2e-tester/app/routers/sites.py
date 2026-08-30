from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db import execute, execute_returning, fetch_all, fetch_one
from app.schemas.models import SiteCreate, SiteOut, SiteUpdate

router = APIRouter(prefix="/api/sites", tags=["sites"])


def _meta_to_str(meta: dict[str, Any] | str | None) -> str | None:
    if meta is None:
        return None
    if isinstance(meta, str):
        return meta
    return json.dumps(meta, ensure_ascii=False)


@router.get("", response_model=list[SiteOut])
async def list_sites() -> list[SiteOut]:
    rows = await fetch_all(
        """
        SELECT id, name, base_url, meta, created_at
        FROM sites
        ORDER BY id ASC
        """
    )
    return [SiteOut(**r) for r in rows]


@router.post("", response_model=SiteOut, status_code=201)
async def create_site(body: SiteCreate) -> SiteOut:
    existing = await fetch_one("SELECT id FROM sites WHERE name = %s", (body.name,))
    if existing is not None:
        raise HTTPException(400, "site name already exists")
    row = await execute_returning(
        """
        INSERT INTO sites (name, base_url, meta)
        VALUES (%s, %s, %s)
        RETURNING id, name, base_url, meta, created_at
        """,
        (body.name, body.base_url.rstrip("/"), _meta_to_str(body.meta)),
    )
    return SiteOut(**row)


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(site_id: int) -> SiteOut:
    row = await fetch_one(
        "SELECT id, name, base_url, meta, created_at FROM sites WHERE id = %s",
        (site_id,),
    )
    if row is None:
        raise HTTPException(404, "site not found")
    return SiteOut(**row)


@router.patch("/{site_id}", response_model=SiteOut)
async def update_site(site_id: int, body: SiteUpdate) -> SiteOut:
    existing = await fetch_one("SELECT * FROM sites WHERE id = %s", (site_id,))
    if existing is None:
        raise HTTPException(404, "site not found")
    name = body.name if body.name is not None else existing["name"]
    base_url = body.base_url.rstrip("/") if body.base_url is not None else existing["base_url"]
    meta = _meta_to_str(body.meta) if body.meta is not None else existing.get("meta")
    if body.name is not None and body.name != existing["name"]:
        clash = await fetch_one(
            "SELECT id FROM sites WHERE name = %s AND id <> %s",
            (body.name, site_id),
        )
        if clash is not None:
            raise HTTPException(400, "site name already exists")
    row = await execute_returning(
        """
        UPDATE sites SET name = %s, base_url = %s, meta = %s
        WHERE id = %s
        RETURNING id, name, base_url, meta, created_at
        """,
        (name, base_url, meta, site_id),
    )
    return SiteOut(**row)


@router.delete("/{site_id}", status_code=204)
async def delete_site(site_id: int) -> None:
    existing = await fetch_one("SELECT id FROM sites WHERE id = %s", (site_id,))
    if existing is None:
        raise HTTPException(404, "site not found")
    await execute("DELETE FROM sites WHERE id = %s", (site_id,))

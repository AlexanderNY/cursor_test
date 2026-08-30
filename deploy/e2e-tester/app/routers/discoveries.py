from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.db import execute, execute_returning, fetch_all, fetch_one
from app.schemas.models import (
    DiscoveryCreate,
    DiscoveryItemOut,
    DiscoveryOut,
    DiscoverySelectBody,
    DiscoveryToScenarioBody,
    ScenarioOut,
)
from app.services.config_builder import (
    LoginConfig,
    PageSectionConfig,
    ScenarioConfigCreate,
    build_scenario_source,
)
from app.services.discovery import selected_items_to_pages
from app.services.discovery_worker import enqueue_discovery
from app.services.scenario_loader import parse_scenario_document

router = APIRouter(prefix="/api/discoveries", tags=["discoveries"])


def _parse_summary(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


async def _build_discovery_out(discovery_id: int, *, with_items: bool = True) -> DiscoveryOut:
    row = await fetch_one("SELECT * FROM discoveries WHERE id = %s", (discovery_id,))
    if row is None:
        raise HTTPException(404, "discovery not found")
    items: list[DiscoveryItemOut] = []
    if with_items:
        item_rows = await fetch_all(
            """
            SELECT * FROM discovery_items
            WHERE discovery_id = %s
            ORDER BY sort_order ASC, id ASC
            """,
            (discovery_id,),
        )
        items = [DiscoveryItemOut(**r) for r in item_rows]
    return DiscoveryOut(
        id=row["id"],
        site_id=row.get("site_id"),
        credentials_id=row.get("credentials_id"),
        base_url=row["base_url"],
        status=row["status"],
        max_pages=row["max_pages"],
        max_depth=row["max_depth"],
        same_origin_only=row["same_origin_only"],
        do_login=row["do_login"],
        error_summary=row.get("error_summary"),
        summary=_parse_summary(row.get("summary_json")),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        created_at=row["created_at"],
        items=items,
    )


@router.get("", response_model=list[DiscoveryOut])
async def list_discoveries() -> list[DiscoveryOut]:
    rows = await fetch_all("SELECT id FROM discoveries ORDER BY id DESC LIMIT 30")
    return [await _build_discovery_out(r["id"], with_items=False) for r in rows]


@router.post("", response_model=DiscoveryOut, status_code=201)
async def create_discovery(body: DiscoveryCreate) -> DiscoveryOut:
    settings = get_settings()
    site_id = body.site_id
    base_url = body.base_url
    site = None
    if site_id is not None:
        site = await fetch_one("SELECT * FROM sites WHERE id = %s", (site_id,))
        if site is None:
            raise HTTPException(400, "site_id not found")
        if not base_url:
            base_url = site["base_url"]
    if not base_url:
        base_url = settings.TARGET_UI_URL
    base_url = str(base_url).rstrip("/")

    if body.credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (body.credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    row = await execute_returning(
        """
        INSERT INTO discoveries (
            site_id, credentials_id, base_url, status,
            max_pages, max_depth, same_origin_only, do_login
        ) VALUES (%s,%s,%s,'queued',%s,%s,%s,%s)
        RETURNING id
        """,
        (
            site_id,
            body.credentials_id,
            base_url,
            body.max_pages,
            body.max_depth,
            body.same_origin_only,
            body.do_login,
        ),
    )
    discovery_id = int(row["id"])
    await enqueue_discovery(discovery_id)
    return await _build_discovery_out(discovery_id)


@router.get("/{discovery_id}", response_model=DiscoveryOut)
async def get_discovery(discovery_id: int) -> DiscoveryOut:
    return await _build_discovery_out(discovery_id)


@router.post("/{discovery_id}/select", response_model=DiscoveryOut)
async def select_items(discovery_id: int, body: DiscoverySelectBody) -> DiscoveryOut:
    existing = await fetch_one("SELECT id FROM discoveries WHERE id = %s", (discovery_id,))
    if existing is None:
        raise HTTPException(404, "discovery not found")
    if not body.item_ids:
        raise HTTPException(400, "item_ids required")
    placeholders = ",".join(["%s"] * len(body.item_ids))
    await execute(
        f"""
        UPDATE discovery_items
        SET selected = %s
        WHERE discovery_id = %s AND id IN ({placeholders})
        """,
        (body.selected, discovery_id, *body.item_ids),
    )
    return await _build_discovery_out(discovery_id)


@router.post("/{discovery_id}/select-all", response_model=DiscoveryOut)
async def select_all(discovery_id: int, body: DiscoverySelectBody) -> DiscoveryOut:
    existing = await fetch_one("SELECT id FROM discoveries WHERE id = %s", (discovery_id,))
    if existing is None:
        raise HTTPException(404, "discovery not found")
    await execute(
        "UPDATE discovery_items SET selected = %s WHERE discovery_id = %s",
        (body.selected, discovery_id),
    )
    return await _build_discovery_out(discovery_id)


@router.get("/{discovery_id}/builder-config")
async def to_builder_config(discovery_id: int, selected_only: bool = True) -> dict[str, Any]:
    disc = await fetch_one("SELECT * FROM discoveries WHERE id = %s", (discovery_id,))
    if disc is None:
        raise HTTPException(404, "discovery not found")
    sql = "SELECT * FROM discovery_items WHERE discovery_id = %s"
    params: tuple[Any, ...] = (discovery_id,)
    if selected_only:
        sql += " AND selected = TRUE"
    sql += " ORDER BY sort_order ASC, id ASC"
    items = await fetch_all(sql, params)
    if not items:
        raise HTTPException(400, "no items selected — отметьте ссылки/кнопки для теста")
    pages = selected_items_to_pages(items)
    return {
        "name": f"discovery_{discovery_id}",
        "base_url": disc["base_url"],
        "site_id": disc.get("site_id"),
        "credentials_id": disc.get("credentials_id"),
        "login": {"enabled": bool(disc.get("do_login"))},
        "pages": pages,
    }


@router.post("/{discovery_id}/to-scenario", response_model=ScenarioOut, status_code=201)
async def to_scenario(discovery_id: int, body: DiscoveryToScenarioBody) -> ScenarioOut:
    disc = await fetch_one("SELECT * FROM discoveries WHERE id = %s", (discovery_id,))
    if disc is None:
        raise HTTPException(404, "discovery not found")

    if body.item_ids:
        placeholders = ",".join(["%s"] * len(body.item_ids))
        items = await fetch_all(
            f"""
            SELECT * FROM discovery_items
            WHERE discovery_id = %s AND id IN ({placeholders})
            ORDER BY sort_order ASC, id ASC
            """,
            (discovery_id, *body.item_ids),
        )
        await execute(
            "UPDATE discovery_items SET selected = FALSE WHERE discovery_id = %s",
            (discovery_id,),
        )
        await execute(
            f"""
            UPDATE discovery_items SET selected = TRUE
            WHERE discovery_id = %s AND id IN ({placeholders})
            """,
            (discovery_id, *body.item_ids),
        )
    else:
        items = await fetch_all(
            """
            SELECT * FROM discovery_items
            WHERE discovery_id = %s AND selected = TRUE
            ORDER BY sort_order ASC, id ASC
            """,
            (discovery_id,),
        )
    if not items:
        raise HTTPException(400, "no items selected")

    pages_raw = selected_items_to_pages(items)
    pages = [PageSectionConfig.model_validate(p) for p in pages_raw]
    cred_id = body.credentials_id if body.credentials_id is not None else disc.get("credentials_id")
    cfg = ScenarioConfigCreate(
        name=body.name,
        base_url=disc["base_url"],
        site_id=disc.get("site_id"),
        credentials_id=cred_id,
        login=LoginConfig(enabled=body.include_login and bool(disc.get("do_login") or cred_id)),
        pages=pages,
    )
    try:
        source = build_scenario_source(cfg)
        parse_scenario_document(source, "json")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if cred_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (cred_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id, site_id, schema_version)
        VALUES (%s, 'json', %s, %s, %s, 2)
        RETURNING id, name, format, source, credentials_id, site_id, schema_version, created_at
        """,
        (body.name, source, cred_id, disc.get("site_id")),
    )
    return ScenarioOut(**row)


@router.delete("/{discovery_id}", status_code=204)
async def delete_discovery(discovery_id: int) -> None:
    existing = await fetch_one("SELECT id FROM discoveries WHERE id = %s", (discovery_id,))
    if existing is None:
        raise HTTPException(404, "discovery not found")
    await execute("DELETE FROM discoveries WHERE id = %s", (discovery_id,))

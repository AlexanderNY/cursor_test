from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response

from app.config import get_settings
from app.db import execute_returning, fetch_all, fetch_one
from app.schemas.models import (
    ArtifactOut,
    RunCreate,
    RunEventOut,
    RunOut,
    RunResultOut,
    RunSummary,
)
from app.services.report import (
    build_report_zip_bytes,
    load_report_payload,
    render_report_html,
)
from app.services.scenario_loader import parse_scenario_document
from app.services.worker import enqueue_run

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _parse_summary(raw: str | None) -> RunSummary | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunSummary.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def _tree_to_models(nodes: list[dict]) -> list[RunResultOut]:
    out: list[RunResultOut] = []
    for node in nodes:
        children = _tree_to_models(node.get("children") or [])
        out.append(
            RunResultOut(
                id=node["id"],
                parent_id=node.get("parent_id"),
                node_type=node["node_type"],
                key=node.get("key"),
                title=node.get("title"),
                status=node["status"],
                error=node.get("error"),
                started_at=node.get("started_at"),
                finished_at=node.get("finished_at"),
                duration_ms=node.get("duration_ms"),
                sort_order=node.get("sort_order") or 0,
                children=children,
            )
        )
    return out


async def _build_run_out(run_id: int) -> RunOut:
    row = await fetch_one("SELECT * FROM runs WHERE id = %s", (run_id,))
    if row is None:
        raise HTTPException(404, "run not found")
    events = await fetch_all(
        "SELECT id, ts, level, message FROM run_events WHERE run_id = %s ORDER BY id ASC",
        (run_id,),
    )
    artifacts = await fetch_all(
        """
        SELECT id, kind, path, step_name, result_id, created_at
        FROM artifacts WHERE run_id = %s ORDER BY id ASC
        """,
        (run_id,),
    )
    result_rows = await fetch_all(
        """
        SELECT id, parent_id, node_type, key, title, status, error,
               started_at, finished_at, duration_ms, sort_order
        FROM run_results WHERE run_id = %s ORDER BY id ASC
        """,
        (run_id,),
    )
    # build_results_tree expects datetime objects — keep as-is for models
    by_id: dict[int, dict] = {}
    roots: list[dict] = []
    for r in result_rows:
        node = {**r, "children": []}
        by_id[r["id"]] = node
    for node in by_id.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    def sort_rec(items: list[dict]) -> None:
        items.sort(key=lambda n: n.get("sort_order") or 0)
        for child in items:
            sort_rec(child["children"])

    sort_rec(roots)

    artifact_out = [
        ArtifactOut(
            id=a["id"],
            kind=a["kind"],
            path=a["path"],
            step_name=a.get("step_name"),
            result_id=a.get("result_id"),
            created_at=a["created_at"],
            url=f"/api/runs/{run_id}/artifacts/{Path(a['path']).name}",
        )
        for a in artifacts
    ]
    return RunOut(
        id=row["id"],
        scenario_id=row["scenario_id"],
        credentials_id=row.get("credentials_id"),
        site_id=row.get("site_id"),
        base_url_snapshot=row.get("base_url_snapshot"),
        summary=_parse_summary(row.get("summary_json")),
        status=row["status"],
        error_summary=row.get("error_summary"),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        created_at=row["created_at"],
        events=[RunEventOut(**e) for e in events],
        artifacts=artifact_out,
        results=_tree_to_models(roots),
    )


async def _resolve_run_target(body: RunCreate, scenario: dict) -> tuple[int | None, str]:
    settings = get_settings()
    site_id = body.site_id if body.site_id is not None else scenario.get("site_id")
    site = None
    if site_id is not None:
        site = await fetch_one("SELECT * FROM sites WHERE id = %s", (site_id,))
        if site is None:
            raise HTTPException(400, "site_id not found")

    if body.base_url:
        return site_id, body.base_url.rstrip("/")

    if scenario.get("format") in ("yaml", "json"):
        try:
            doc = parse_scenario_document(scenario["source"], scenario["format"])
            if doc.base_url:
                return site_id, doc.base_url.rstrip("/")
            if doc.site and site is None:
                by_name = await fetch_one("SELECT * FROM sites WHERE name = %s", (doc.site,))
                if by_name is not None:
                    site_id = int(by_name["id"])
                    site = by_name
        except ValueError:
            pass

    if site is not None:
        return site_id, str(site["base_url"]).rstrip("/")

    return site_id, settings.TARGET_UI_URL.rstrip("/")


@router.get("", response_model=list[RunOut])
async def list_runs() -> list[RunOut]:
    rows = await fetch_all(
        """
        SELECT id FROM runs ORDER BY id DESC LIMIT 50
        """
    )
    return [await _build_run_out(r["id"]) for r in rows]


@router.post("", response_model=RunOut, status_code=201)
async def create_run(body: RunCreate) -> RunOut:
    scenario = await fetch_one("SELECT * FROM scenarios WHERE id = %s", (body.scenario_id,))
    if scenario is None:
        raise HTTPException(404, "scenario not found")

    cred_id = body.credentials_id
    if cred_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (cred_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")
    else:
        cred_id = scenario.get("credentials_id")

    site_id, base_url = await _resolve_run_target(body, scenario)

    row = await execute_returning(
        """
        INSERT INTO runs (scenario_id, credentials_id, site_id, base_url_snapshot, status)
        VALUES (%s, %s, %s, %s, 'queued')
        RETURNING id
        """,
        (body.scenario_id, cred_id, site_id, base_url),
    )
    run_id = int(row["id"])
    await enqueue_run(run_id)
    return await _build_run_out(run_id)


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: int) -> RunOut:
    return await _build_run_out(run_id)


@router.get("/{run_id}/report.html")
async def get_report_html(run_id: int) -> HTMLResponse:
    payload = await load_report_payload(run_id)
    if payload is None:
        raise HTTPException(404, "run not found")
    url_map = {
        str(art.get("filename")): f"/api/runs/{run_id}/artifacts/{art.get('filename')}"
        for art in (payload.get("artifacts") or [])
        if art.get("filename")
    }
    html_doc = render_report_html(payload, artifact_url_map=url_map)
    return HTMLResponse(html_doc)


@router.get("/{run_id}/report.zip")
async def get_report_zip(run_id: int) -> Response:
    data = await build_report_zip_bytes(run_id)
    if data is None:
        raise HTTPException(404, "run not found")
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="e2e-run-{run_id}.zip"'},
    )


@router.get("/{run_id}/artifacts/{filename}")
async def get_artifact(run_id: int, filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "invalid filename")
    art = await fetch_one(
        "SELECT path FROM artifacts WHERE run_id = %s AND path LIKE %s",
        (run_id, f"%/{filename}"),
    )
    if art is None:
        art = await fetch_one(
            "SELECT path FROM artifacts WHERE run_id = %s AND path = %s",
            (run_id, f"{run_id}/{filename}"),
        )
    if art is None:
        raise HTTPException(404, "artifact not found")

    settings = get_settings()
    file_path = settings.artifacts_path / art["path"]
    if not file_path.is_file():
        raise HTTPException(404, "artifact file missing on disk")
    return FileResponse(file_path, media_type="image/png")

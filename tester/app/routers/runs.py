from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.db import execute_returning, fetch_all, fetch_one
from app.schemas.models import ArtifactOut, RunCreate, RunEventOut, RunOut
from app.services.worker import enqueue_run

router = APIRouter(prefix="/api/runs", tags=["runs"])


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
        SELECT id, kind, path, step_name, created_at
        FROM artifacts WHERE run_id = %s ORDER BY id ASC
        """,
        (run_id,),
    )
    artifact_out = [
        ArtifactOut(
            **a,
            url=f"/api/runs/{run_id}/artifacts/{Path(a['path']).name}",
        )
        for a in artifacts
    ]
    return RunOut(
        **{k: row[k] for k in (
            "id",
            "scenario_id",
            "credentials_id",
            "status",
            "error_summary",
            "started_at",
            "finished_at",
            "created_at",
        )},
        events=[RunEventOut(**e) for e in events],
        artifacts=artifact_out,
    )


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
    scenario = await fetch_one("SELECT id, credentials_id FROM scenarios WHERE id = %s", (body.scenario_id,))
    if scenario is None:
        raise HTTPException(404, "scenario not found")

    cred_id = body.credentials_id
    if cred_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (cred_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")
    else:
        cred_id = scenario.get("credentials_id")

    row = await execute_returning(
        """
        INSERT INTO runs (scenario_id, credentials_id, status)
        VALUES (%s, %s, 'queued')
        RETURNING id
        """,
        (body.scenario_id, cred_id),
    )
    run_id = int(row["id"])
    await enqueue_run(run_id)
    return await _build_run_out(run_id)


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: int) -> RunOut:
    return await _build_run_out(run_id)


@router.get("/{run_id}/artifacts/{filename}")
async def get_artifact(run_id: int, filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "invalid filename")
    art = await fetch_one(
        "SELECT path FROM artifacts WHERE run_id = %s AND path LIKE %s",
        (run_id, f"%/{filename}"),
    )
    if art is None:
        # also allow exact path match when stored as run_id/name
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

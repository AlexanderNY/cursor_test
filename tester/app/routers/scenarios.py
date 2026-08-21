from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db import execute, execute_returning, fetch_all, fetch_one
from app.schemas.models import ScenarioCreate, ScenarioOut
from app.services.scenario_loader import parse_scenario_document, validate_playwright_script

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


def _detect_format(filename: str | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    if not filename:
        return "yaml"
    lower = filename.lower()
    if lower.endswith(".py"):
        return "playwright_py"
    if lower.endswith(".json"):
        return "json"
    return "yaml"


def _validate_source(fmt: str, source: str) -> None:
    if fmt in ("yaml", "json"):
        parse_scenario_document(source, fmt)
    elif fmt == "playwright_py":
        validate_playwright_script(source)
    else:
        raise ValueError(f"unsupported format: {fmt}")


@router.get("", response_model=list[ScenarioOut])
async def list_scenarios() -> list[ScenarioOut]:
    rows = await fetch_all(
        """
        SELECT id, name, format, source, credentials_id, created_at
        FROM scenarios
        ORDER BY id DESC
        """
    )
    return [ScenarioOut(**r) for r in rows]


@router.post("", response_model=ScenarioOut, status_code=201)
async def create_scenario(body: ScenarioCreate) -> ScenarioOut:
    try:
        _validate_source(body.format, body.source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if body.credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (body.credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, format, source, credentials_id, created_at
        """,
        (body.name, body.format, body.source, body.credentials_id),
    )
    return ScenarioOut(**row)


@router.post("/upload", response_model=ScenarioOut, status_code=201)
async def upload_scenario(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    format: str | None = Form(None),
    credentials_id: int | None = Form(None),
) -> ScenarioOut:
    raw = await file.read()
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "file must be UTF-8 text") from exc

    fmt = _detect_format(file.filename, format)
    scenario_name = name or (file.filename or "uploaded")
    try:
        _validate_source(fmt, source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, format, source, credentials_id, created_at
        """,
        (scenario_name, fmt, source, credentials_id),
    )
    return ScenarioOut(**row)


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(scenario_id: int) -> ScenarioOut:
    row = await fetch_one(
        """
        SELECT id, name, format, source, credentials_id, created_at
        FROM scenarios WHERE id = %s
        """,
        (scenario_id,),
    )
    if row is None:
        raise HTTPException(404, "scenario not found")
    return ScenarioOut(**row)


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: int) -> None:
    existing = await fetch_one("SELECT id FROM scenarios WHERE id = %s", (scenario_id,))
    if existing is None:
        raise HTTPException(404, "scenario not found")
    await execute("DELETE FROM scenarios WHERE id = %s", (scenario_id,))

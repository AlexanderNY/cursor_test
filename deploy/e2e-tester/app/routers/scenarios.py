from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db import execute, execute_returning, fetch_all, fetch_one
from app.schemas.models import ScenarioCreate, ScenarioOut
from app.services.config_builder import ScenarioConfigCreate, build_scenario_source
from app.services.crypto import encrypt_payload
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


def _validate_and_version(fmt: str, source: str) -> int:
    if fmt in ("yaml", "json"):
        doc = parse_scenario_document(source, fmt)
        return int(doc.schema_version)
    if fmt == "playwright_py":
        validate_playwright_script(source)
        return 1
    raise ValueError(f"unsupported format: {fmt}")


async def _resolve_site_id(site_id: int | None, fmt: str, source: str) -> int | None:
    if site_id is not None:
        site = await fetch_one("SELECT id FROM sites WHERE id = %s", (site_id,))
        if site is None:
            raise HTTPException(400, "site_id not found")
        return site_id
    if fmt not in ("yaml", "json"):
        return None
    try:
        doc = parse_scenario_document(source, fmt)
    except ValueError:
        return None
    if not doc.site:
        return None
    by_name = await fetch_one("SELECT id FROM sites WHERE name = %s", (doc.site,))
    return int(by_name["id"]) if by_name else None


@router.get("", response_model=list[ScenarioOut])
async def list_scenarios() -> list[ScenarioOut]:
    rows = await fetch_all(
        """
        SELECT id, name, format, source, credentials_id, site_id, schema_version, created_at
        FROM scenarios
        ORDER BY id DESC
        """
    )
    return [ScenarioOut(**r) for r in rows]


async def _ensure_site_for_config(cfg: ScenarioConfigCreate) -> int | None:
    if cfg.site_id is not None:
        site = await fetch_one("SELECT id FROM sites WHERE id = %s", (cfg.site_id,))
        if site is None:
            raise HTTPException(400, "site_id not found")
        return int(site["id"])

    site_name = cfg.site_name or cfg.name
    meta = {
        "login": {
            "path": cfg.login.path,
            "username_selector": cfg.login.username_selector,
            "password_selector": cfg.login.password_selector,
            "submit_selector": cfg.login.submit_selector,
        }
    }

    existing = await fetch_one("SELECT id FROM sites WHERE name = %s", (site_name,))
    if existing is not None:
        await execute(
            "UPDATE sites SET base_url = %s, meta = %s WHERE id = %s",
            (cfg.base_url.rstrip("/"), json.dumps(meta, ensure_ascii=False), existing["id"]),
        )
        return int(existing["id"])

    row = await execute_returning(
        """
        INSERT INTO sites (name, base_url, meta)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (site_name, cfg.base_url.rstrip("/"), json.dumps(meta, ensure_ascii=False)),
    )
    return int(row["id"])


async def _ensure_credentials_for_config(cfg: ScenarioConfigCreate) -> int | None:
    if cfg.credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (cfg.credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")
        return int(cred["id"])

    if not cfg.create_credential:
        return None
    if not cfg.username or not cfg.password:
        raise HTTPException(400, "username and password required when create_credential=true")

    cred_name = cfg.credential_name or f"{cfg.name}_login"
    existing = await fetch_one("SELECT id FROM credentials WHERE name = %s", (cred_name,))
    payload = {"username": cfg.username, "password": cfg.password}
    try:
        ciphertext = encrypt_payload(payload)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc

    if existing is not None:
        await execute(
            """
            UPDATE credentials
            SET cred_type = 'password', payload_encrypted = %s, meta = %s
            WHERE id = %s
            """,
            (ciphertext, f"from config:{cfg.name}", existing["id"]),
        )
        return int(existing["id"])

    row = await execute_returning(
        """
        INSERT INTO credentials (name, cred_type, payload_encrypted, meta)
        VALUES (%s, 'password', %s, %s)
        RETURNING id
        """,
        (cred_name, ciphertext, f"from config:{cfg.name}"),
    )
    return int(row["id"])


@router.post("/preview-config")
async def preview_config(body: ScenarioConfigCreate) -> dict:
    try:
        source = build_scenario_source(body)
        parse_scenario_document(source, "json")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"format": "json", "source": source}


@router.post("/from-config", response_model=ScenarioOut, status_code=201)
async def create_from_config(body: ScenarioConfigCreate) -> ScenarioOut:
    try:
        source = build_scenario_source(body)
        schema_version = _validate_and_version("json", source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    site_id = await _ensure_site_for_config(body)
    credentials_id = await _ensure_credentials_for_config(body)

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id, site_id, schema_version)
        VALUES (%s, 'json', %s, %s, %s, %s)
        RETURNING id, name, format, source, credentials_id, site_id, schema_version, created_at
        """,
        (body.name, source, credentials_id, site_id, schema_version),
    )
    return ScenarioOut(**row)


@router.post("", response_model=ScenarioOut, status_code=201)
async def create_scenario(body: ScenarioCreate) -> ScenarioOut:
    try:
        schema_version = _validate_and_version(body.format, body.source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if body.credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (body.credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    site_id = await _resolve_site_id(body.site_id, body.format, body.source)

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id, site_id, schema_version)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, name, format, source, credentials_id, site_id, schema_version, created_at
        """,
        (body.name, body.format, body.source, body.credentials_id, site_id, schema_version),
    )
    return ScenarioOut(**row)


@router.post("/upload", response_model=ScenarioOut, status_code=201)
async def upload_scenario(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    format: str | None = Form(None),
    credentials_id: int | None = Form(None),
    site_id: int | None = Form(None),
) -> ScenarioOut:
    raw = await file.read()
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "file must be UTF-8 text") from exc

    fmt = _detect_format(file.filename, format)
    scenario_name = name or (file.filename or "uploaded")
    try:
        schema_version = _validate_and_version(fmt, source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if credentials_id is not None:
        cred = await fetch_one("SELECT id FROM credentials WHERE id = %s", (credentials_id,))
        if cred is None:
            raise HTTPException(400, "credentials_id not found")

    resolved_site = await _resolve_site_id(site_id, fmt, source)

    row = await execute_returning(
        """
        INSERT INTO scenarios (name, format, source, credentials_id, site_id, schema_version)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, name, format, source, credentials_id, site_id, schema_version, created_at
        """,
        (scenario_name, fmt, source, credentials_id, resolved_site, schema_version),
    )
    return ScenarioOut(**row)


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(scenario_id: int) -> ScenarioOut:
    row = await fetch_one(
        """
        SELECT id, name, format, source, credentials_id, site_id, schema_version, created_at
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

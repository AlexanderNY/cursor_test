"""API: несколько версий HH-резюме + sync PDF/DOCX export."""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from auth import require_site_admin, require_user
from database import get_db_connection, release_db_connection
from rate_limit import enforce_rate_limit
from services.resume_export import build_docx_bytes, build_pdf_bytes, render_resume_html
from services.resume_questionnaire import (
    apply_questionnaire_to_template,
    get_questionnaire,
    validate_answers,
)
from services.resume_skills import (
    branch_completion_hints,
    build_gap_catalog,
    generate_skills_from_progress,
    suggest_specialization,
)
from services.resume_strength import compute_resume_strength
from services.runtime_settings import (
    feature_enabled,
    load_settings,
    public_settings_view,
    save_settings,
)
from services.text_sanitize import sanitize_plain_text
from services import resume_ai
from storage_client import (
    build_api_file_url,
    expires_iso,
    get_resume_storage,
    safe_filename,
)

router = APIRouter(prefix="/resume", tags=["resume"])

EMPLOYMENT_ALLOWED = {"full", "part", "project", "volunteer", "internship"}
WORK_FORMAT_ALLOWED = {"office", "remote", "hybrid", "travel"}
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

RESUME_SELECT = """
    id, user_id, version_name, title, specialization, salary_amount, salary_currency,
    employment_types, work_formats, about, selected_skill_keys, generated_skills,
    questionnaire_answers, created_at, updated_at
"""


class ResumeCreateIn(BaseModel):
    version_name: str = Field(default="Основное", min_length=1, max_length=120)
    copy_from: Optional[str] = None


class ResumeUpdateIn(BaseModel):
    version_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    title: Optional[str] = Field(default=None, max_length=255)
    specialization: Optional[str] = Field(default=None, max_length=255)
    salary_amount: Optional[int] = Field(default=None, ge=0, le=100_000_000)
    salary_currency: Optional[str] = Field(default=None, max_length=8)
    employment_types: Optional[list[str]] = None
    work_formats: Optional[list[str]] = None
    about: Optional[str] = Field(default=None, max_length=8000)
    selected_skill_keys: Optional[list[str]] = None


class ResumeGenerateIn(BaseModel):
    selected_skill_keys: Optional[list[str]] = None
    persist: bool = True


class QuestionnaireApplyIn(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    persist: bool = True


class ResumeExportIn(BaseModel):
    format: str = Field(..., pattern=r"^(pdf|docx)$")


class ImproveAboutIn(BaseModel):
    text: Optional[str] = Field(default=None, max_length=8000)
    persist: bool = True


class SkillGapIn(BaseModel):
    target_role: Optional[str] = Field(default=None, max_length=255)


class CoverLetterIn(BaseModel):
    vacancy_text: str = Field(..., min_length=20, max_length=8000)


class MockInterviewStartIn(BaseModel):
    count: int = Field(default=5, ge=3, le=5)


class MockInterviewEvalIn(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=1, max_length=4000)
    skill_key: Optional[str] = Field(default=None, max_length=64)


def _parse_resume_id(raw: str) -> UUID:
    text = (raw or "").strip()
    if not UUID_RE.match(text):
        raise HTTPException(status_code=400, detail="Invalid resume id")
    return UUID(text)


def _normalize_string_list(values: Optional[list[str]], allowed: set[str]) -> list[str]:
    if values is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        key = str(raw or "").strip().lower()
        if key not in allowed or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _json_object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _row_profile(row: tuple, *, email: str = "") -> dict[str, Any]:
    birth = row[5]
    return {
        "lastName": str(row[1] or ""),
        "firstName": str(row[2] or ""),
        "patronymic": str(row[3] or ""),
        "phone": str(row[4] or ""),
        "birthDate": birth.isoformat() if hasattr(birth, "isoformat") else (str(birth) if birth else None),
        "city": str(row[6] or ""),
        "citizenship": str(row[7] or ""),
        "readyForTrips": bool(row[8]),
        "hasPhoto": bool(row[9]),
        "email": email,
        "updatedAt": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10] or ""),
    }


def _empty_profile(*, email: str = "") -> dict[str, Any]:
    return {
        "lastName": "",
        "firstName": "",
        "patronymic": "",
        "phone": "",
        "birthDate": None,
        "city": "",
        "citizenship": "",
        "readyForTrips": False,
        "hasPhoto": False,
        "email": email,
        "updatedAt": None,
    }


def _row_resume(row: tuple) -> dict[str, Any]:
    return {
        "id": str(row[0]),
        "userId": int(row[1]),
        "versionName": str(row[2] or "Основное"),
        "title": str(row[3] or ""),
        "specialization": str(row[4] or ""),
        "salaryAmount": int(row[5]) if row[5] is not None else None,
        "salaryCurrency": str(row[6] or "RUB"),
        "employmentTypes": [str(x) for x in _json_list(row[7])],
        "workFormats": [str(x) for x in _json_list(row[8])],
        "about": str(row[9] or ""),
        "selectedSkillKeys": [str(x) for x in _json_list(row[10])],
        "generatedSkills": _json_list(row[11]),
        "questionnaireAnswers": _json_object(row[12]),
        "createdAt": row[13].isoformat() if hasattr(row[13], "isoformat") else str(row[13] or ""),
        "updatedAt": row[14].isoformat() if hasattr(row[14], "isoformat") else str(row[14] or ""),
    }


def _row_resume_summary(row: tuple) -> dict[str, Any]:
    return {
        "id": str(row[0]),
        "versionName": str(row[1] or "Основное"),
        "title": str(row[2] or ""),
        "specialization": str(row[3] or ""),
        "updatedAt": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4] or ""),
    }


def _empty_resume(*, version_name: str = "Основное") -> dict[str, Any]:
    return {
        "id": "",
        "userId": 0,
        "versionName": version_name,
        "title": "",
        "specialization": "",
        "salaryAmount": None,
        "salaryCurrency": "RUB",
        "employmentTypes": [],
        "workFormats": [],
        "about": "",
        "selectedSkillKeys": [],
        "generatedSkills": [],
        "questionnaireAnswers": {},
        "createdAt": None,
        "updatedAt": None,
    }


async def _fetch_completed_slugs(user_id: int) -> list[str]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT slug FROM site_learn_progress WHERE user_id = %s",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [str(r[0]) for r in rows]
    finally:
        await release_db_connection(conn)


async def _fetch_profile_row(user_id: int) -> Optional[tuple]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, last_name, first_name, patronymic, phone, birth_date,
                       city, citizenship, ready_for_trips, photo_key, updated_at
                FROM site_user_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return await cur.fetchone()
    finally:
        await release_db_connection(conn)


async def _fetch_resume_owned(resume_id: UUID, user_id: int) -> Optional[tuple]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {RESUME_SELECT}
                FROM site_resumes
                WHERE id = %s AND user_id = %s
                """,
                (str(resume_id), user_id),
            )
            return await cur.fetchone()
    finally:
        await release_db_connection(conn)


async def _require_resume(resume_id: UUID, user_id: int) -> dict[str, Any]:
    row = await _fetch_resume_owned(resume_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _row_resume(row)


def _skills_for_resume(resume: dict[str, Any], completed: list[str]) -> list[Any]:
    selected = resume["selectedSkillKeys"] or None
    skills = resume["generatedSkills"]
    if not skills:
        return generate_skills_from_progress(completed, selected_keys=selected)
    if selected:
        allow = set(selected)
        return [s for s in skills if isinstance(s, dict) and s.get("key") in allow]
    return skills


@router.get("")
async def list_resumes(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await require_user(authorization)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, version_name, title, specialization, updated_at
                FROM site_resumes
                WHERE user_id = %s
                ORDER BY updated_at DESC, created_at DESC
                """,
                (user["user_id"],),
            )
            rows = await cur.fetchall()
    finally:
        await release_db_connection(conn)
    return {"items": [_row_resume_summary(r) for r in rows]}


@router.post("")
async def create_resume(
    body: ResumeCreateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    version_name = body.version_name.strip() or "Основное"

    source: Optional[dict[str, Any]] = None
    if body.copy_from:
        source = await _require_resume(_parse_resume_id(body.copy_from), user_id)
        version_name = body.version_name.strip() or f"Копия · {source['versionName']}"

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            if source:
                await cur.execute(
                    f"""
                    INSERT INTO site_resumes (
                        user_id, version_name, title, specialization, salary_amount,
                        salary_currency, employment_types, work_formats, about,
                        selected_skill_keys, generated_skills, questionnaire_answers
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s::jsonb, %s::jsonb, %s,
                        %s::jsonb, %s::jsonb, %s::jsonb
                    )
                    RETURNING {RESUME_SELECT}
                    """,
                    (
                        user_id,
                        version_name[:120],
                        source["title"],
                        source["specialization"],
                        source["salaryAmount"],
                        source["salaryCurrency"],
                        json.dumps(source["employmentTypes"], ensure_ascii=False),
                        json.dumps(source["workFormats"], ensure_ascii=False),
                        source["about"],
                        json.dumps(source["selectedSkillKeys"], ensure_ascii=False),
                        json.dumps(source["generatedSkills"], ensure_ascii=False),
                        json.dumps(source["questionnaireAnswers"], ensure_ascii=False),
                    ),
                )
            else:
                await cur.execute(
                    f"""
                    INSERT INTO site_resumes (user_id, version_name)
                    VALUES (%s, %s)
                    RETURNING {RESUME_SELECT}
                    """,
                    (user_id, version_name[:120]),
                )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    assert row is not None
    return _row_resume(row)


@router.get("/questionnaire")
async def questionnaire_schema() -> dict[str, Any]:
    return get_questionnaire()


@router.get("/admin/settings")
async def admin_get_settings(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await require_site_admin(authorization)
    doc = await load_settings(force=True)
    return public_settings_view(doc)


@router.put("/admin/settings")
async def admin_put_settings(
    body: dict[str, Any],
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    await require_site_admin(authorization)
    payload = body.get("settings") if isinstance(body.get("settings"), dict) else body
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Expected settings object")
    doc = await save_settings(payload)
    return public_settings_view(doc)


@router.get("/files/{file_id}")
async def download_export_file(
    file_id: str,
    authorization: Optional[str] = Header(None),
) -> Response:
    user = await require_user(authorization)
    export_id = _parse_resume_id(file_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT storage_key, file_name, format, expires_at
                FROM site_resume_exports
                WHERE id = %s AND user_id = %s
                """,
                (str(export_id), user["user_id"]),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    expires_at = row[3]
    if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is None:
        from datetime import timezone as tz

        expires_at = expires_at.replace(tzinfo=tz.utc)
    from datetime import datetime, timezone

    if expires_at and datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=410, detail="Download link expired")

    storage_key = str(row[0] or "")
    file_name = str(row[1] or "resume.bin")
    fmt = str(row[2] or "pdf")
    media = (
        "application/pdf"
        if fmt == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    storage = get_resume_storage()
    data: Optional[bytes] = None
    if storage_key.startswith("local:"):
        data = storage.read_local(storage_key[len("local:") :])
    elif storage_key.startswith("s3:"):
        key = storage_key[len("s3:") :]
        url = storage.presign_get(key, expires_seconds=300)
        if url:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.content
    if not data:
        raise HTTPException(status_code=404, detail="File content missing")

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    return await _require_resume(_parse_resume_id(resume_id), int(user["user_id"]))


@router.put("/{resume_id}")
async def put_resume(
    resume_id: str,
    body: ResumeUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    rid = _parse_resume_id(resume_id)
    cur = await _require_resume(rid, user_id)

    version_name = (
        body.version_name.strip() if body.version_name is not None else cur["versionName"]
    )
    title = body.title.strip() if body.title is not None else cur["title"]
    specialization = (
        body.specialization.strip() if body.specialization is not None else cur["specialization"]
    )
    dumped = body.model_dump(exclude_unset=True)
    salary_amount = (
        dumped["salary_amount"] if "salary_amount" in dumped else cur["salaryAmount"]
    )
    salary_currency = (
        body.salary_currency.strip().upper()
        if body.salary_currency is not None
        else cur["salaryCurrency"]
    ) or "RUB"
    employment_types = (
        _normalize_string_list(body.employment_types, EMPLOYMENT_ALLOWED)
        if body.employment_types is not None
        else cur["employmentTypes"]
    )
    work_formats = (
        _normalize_string_list(body.work_formats, WORK_FORMAT_ALLOWED)
        if body.work_formats is not None
        else cur["workFormats"]
    )
    about = (
        sanitize_plain_text(body.about)
        if body.about is not None
        else cur["about"]
    )
    selected_skill_keys = (
        [str(k).strip() for k in body.selected_skill_keys if str(k).strip()]
        if body.selected_skill_keys is not None
        else cur["selectedSkillKeys"]
    )

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur_db:
            await cur_db.execute(
                f"""
                UPDATE site_resumes SET
                    version_name = %s,
                    title = %s,
                    specialization = %s,
                    salary_amount = %s,
                    salary_currency = %s,
                    employment_types = %s::jsonb,
                    work_formats = %s::jsonb,
                    about = %s,
                    selected_skill_keys = %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                RETURNING {RESUME_SELECT}
                """,
                (
                    version_name[:120],
                    title,
                    specialization,
                    salary_amount,
                    salary_currency,
                    json.dumps(employment_types, ensure_ascii=False),
                    json.dumps(work_formats, ensure_ascii=False),
                    about,
                    json.dumps(selected_skill_keys, ensure_ascii=False),
                    str(rid),
                    user_id,
                ),
            )
            row = await cur_db.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _row_resume(row)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    rid = _parse_resume_id(resume_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM site_resumes WHERE id = %s AND user_id = %s RETURNING id",
                (str(rid), user["user_id"]),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"ok": True, "id": str(row[0])}


@router.get("/{resume_id}/preview")
async def resume_preview(
    resume_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "preview")
    await load_settings()
    email = str(user.get("email") or "")
    resume, profile_row, completed = await asyncio.gather(
        _require_resume(_parse_resume_id(resume_id), user_id),
        _fetch_profile_row(user_id),
        _fetch_completed_slugs(user_id),
    )
    profile = _row_profile(profile_row, email=email) if profile_row else _empty_profile(email=email)
    skills = _skills_for_resume(resume, completed)
    hints = branch_completion_hints(completed)
    suggested = suggest_specialization(completed)
    strength = compute_resume_strength(
        has_photo=bool(profile.get("hasPhoto")),
        about=resume.get("about") or "",
        specialization=resume.get("specialization") or suggested or "",
        completed_slugs=completed,
    )
    return {
        "profile": profile,
        "resume": resume,
        "skills": skills,
        "branchHints": hints,
        "suggestedSpecialization": suggested,
        "completedCount": len(completed),
        "completedSlugs": completed,
        "username": user["username"],
        "strength": strength,
    }


@router.get("/{resume_id}/strength")
async def resume_strength(
    resume_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    resume = await _require_resume(_parse_resume_id(resume_id), user_id)
    profile_row = await _fetch_profile_row(user_id)
    completed = await _fetch_completed_slugs(user_id)
    has_photo = bool(profile_row[9]) if profile_row else False
    return compute_resume_strength(
        has_photo=has_photo,
        about=resume.get("about") or "",
        specialization=resume.get("specialization")
        or suggest_specialization(completed)
        or "",
        completed_slugs=completed,
    )


@router.post("/{resume_id}/generate")
async def generate_resume(
    resume_id: str,
    body: ResumeGenerateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "generate")
    rid = _parse_resume_id(resume_id)
    await _require_resume(rid, user_id)
    completed = await _fetch_completed_slugs(user_id)
    selected = body.selected_skill_keys
    skills = generate_skills_from_progress(completed, selected_keys=selected)
    hints = branch_completion_hints(completed)
    suggested = suggest_specialization(completed)

    if body.persist:
        keys_to_store = selected if selected is not None else [s["key"] for s in skills]
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE site_resumes SET
                        generated_skills = %s::jsonb,
                        selected_skill_keys = %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        json.dumps(skills, ensure_ascii=False),
                        json.dumps(keys_to_store, ensure_ascii=False),
                        str(rid),
                        user_id,
                    ),
                )
        finally:
            await release_db_connection(conn)

    return {
        "skills": skills,
        "branchHints": hints,
        "suggestedSpecialization": suggested,
        "completedCount": len(completed),
    }


def _require_feature(name: str) -> None:
    if not feature_enabled(name, True):
        raise HTTPException(status_code=403, detail=f"Feature disabled: {name}")


def _ai_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    msg = str(exc) or "AI недоступен"
    if "недоступен" in msg.lower() or "ai" in msg.lower():
        return HTTPException(status_code=503, detail=msg)
    return HTTPException(status_code=502, detail=msg)


@router.post("/{resume_id}/ai/improve-about")
async def ai_improve_about(
    resume_id: str,
    body: ImproveAboutIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "ai")
    _require_feature("aiImproveAbout")
    rid = _parse_resume_id(resume_id)
    resume = await _require_resume(rid, user_id)
    completed = await _fetch_completed_slugs(user_id)
    skills = _skills_for_resume(resume, completed)
    source = (body.text if body.text is not None else resume["about"] or "").strip()
    try:
        improved = await resume_ai.improve_about(
            source,
            specialization=resume["specialization"] or resume["title"] or "",
            skills=[str(s.get("display") or s.get("name") or "") for s in skills],
        )
    except Exception as exc:
        raise _ai_http_error(exc) from exc

    improved = sanitize_plain_text(improved)

    persisted = False
    if body.persist:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE site_resumes SET
                        about = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    """,
                    (improved, str(rid), user_id),
                )
            persisted = True
        finally:
            await release_db_connection(conn)

    return {"about": improved, "persisted": persisted}


@router.post("/{resume_id}/ai/skill-gap")
async def ai_skill_gap(
    resume_id: str,
    body: SkillGapIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "ai")
    _require_feature("aiSkillGap")
    resume = await _require_resume(_parse_resume_id(resume_id), user_id)
    completed = await _fetch_completed_slugs(user_id)
    skills = _skills_for_resume(resume, completed)
    selected_keys = resume["selectedSkillKeys"] or [s["key"] for s in skills]
    catalog = build_gap_catalog(completed, selected_keys=selected_keys)
    target = (body.target_role or "").strip() or resume["specialization"] or resume["title"] or ""
    try:
        result = await resume_ai.analyze_skill_gap(
            target_role=target,
            selected_skills=skills,
            completed_slugs=completed,
            catalog=catalog,
        )
    except Exception as exc:
        raise _ai_http_error(exc) from exc
    return result


@router.post("/{resume_id}/ai/cover-letter")
async def ai_cover_letter(
    resume_id: str,
    body: CoverLetterIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "ai")
    _require_feature("aiCoverLetter")
    email = str(user.get("email") or "")
    resume = await _require_resume(_parse_resume_id(resume_id), user_id)
    profile_row = await _fetch_profile_row(user_id)
    profile = _row_profile(profile_row, email=email) if profile_row else _empty_profile(email=email)
    completed = await _fetch_completed_slugs(user_id)
    skills = _skills_for_resume(resume, completed)
    full_name = " ".join(
        p
        for p in [
            profile.get("lastName") or "",
            profile.get("firstName") or "",
            profile.get("patronymic") or "",
        ]
        if p
    ).strip() or user.get("username") or ""
    resume_ctx = {
        "fullName": full_name,
        "title": resume["title"],
        "specialization": resume["specialization"],
        "about": resume["about"],
        "skills": [s.get("display") or s.get("name") for s in skills],
        "employmentTypes": resume["employmentTypes"],
        "workFormats": resume["workFormats"],
        "salaryAmount": resume["salaryAmount"],
        "city": profile.get("city") or "",
    }
    try:
        letter = await resume_ai.generate_cover_letter(
            resume_ctx=resume_ctx,
            vacancy_text=body.vacancy_text,
        )
    except Exception as exc:
        raise _ai_http_error(exc) from exc
    return {"letter": letter}


@router.post("/{resume_id}/ai/mock-interview")
async def ai_mock_interview_start(
    resume_id: str,
    body: MockInterviewStartIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "ai")
    _require_feature("aiMockInterview")
    resume = await _require_resume(_parse_resume_id(resume_id), user_id)
    completed = await _fetch_completed_slugs(user_id)
    skills = _skills_for_resume(resume, completed)
    if body.count < len(skills):
        skills = skills[: body.count]
    try:
        questions = await resume_ai.generate_mock_interview(
            specialization=resume["specialization"] or resume["title"] or "",
            skills=skills,
        )
    except Exception as exc:
        raise _ai_http_error(exc) from exc
    return {"questions": questions[: body.count]}


@router.post("/{resume_id}/ai/mock-interview/evaluate")
async def ai_mock_interview_evaluate(
    resume_id: str,
    body: MockInterviewEvalIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "ai")
    _require_feature("aiMockInterview")
    await _require_resume(_parse_resume_id(resume_id), user_id)
    try:
        result = await resume_ai.evaluate_mock_answer(
            question=body.question,
            answer=body.answer,
            skill_key=body.skill_key or "",
        )
    except Exception as exc:
        raise _ai_http_error(exc) from exc
    return result


@router.post("/{resume_id}/questionnaire/apply")
async def questionnaire_apply(
    resume_id: str,
    body: QuestionnaireApplyIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    rid = _parse_resume_id(resume_id)
    existing = await _require_resume(rid, user_id)
    answers = body.answers if isinstance(body.answers, dict) else {}
    errors = validate_answers(answers)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    completed = await _fetch_completed_slugs(user_id)
    hints = branch_completion_hints(completed)
    draft = apply_questionnaire_to_template(answers, branch_hints=hints)
    draft["about"] = sanitize_plain_text(draft.get("about") or "")

    resume_out = {
        **existing,
        "title": draft["title"],
        "specialization": draft["specialization"],
        "salaryAmount": draft["salaryAmount"],
        "salaryCurrency": draft["salaryCurrency"],
        "employmentTypes": draft["employmentTypes"],
        "workFormats": draft["workFormats"],
        "about": draft["about"],
        "questionnaireAnswers": answers,
    }

    if body.persist:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE site_resumes SET
                        title = %s,
                        specialization = %s,
                        salary_amount = %s,
                        salary_currency = %s,
                        employment_types = %s::jsonb,
                        work_formats = %s::jsonb,
                        about = %s,
                        questionnaire_answers = %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING {RESUME_SELECT}
                    """,
                    (
                        draft["title"],
                        draft["specialization"],
                        draft["salaryAmount"],
                        draft["salaryCurrency"],
                        json.dumps(draft["employmentTypes"], ensure_ascii=False),
                        json.dumps(draft["workFormats"], ensure_ascii=False),
                        draft["about"],
                        json.dumps(answers, ensure_ascii=False),
                        str(rid),
                        user_id,
                    ),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume_out = _row_resume(row)

    return {
        "resume": resume_out,
        "branchHints": hints,
        "completedCount": len(completed),
        "suggestedSpecialization": draft["specialization"],
    }


@router.post("/{resume_id}/export")
async def export_resume(
    resume_id: str,
    body: ResumeExportIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_rate_limit(user_id, "export")
    _require_feature("exportEnabled")
    rid = _parse_resume_id(resume_id)
    resume = await _require_resume(rid, user_id)
    email = str(user.get("email") or "")
    profile_row = await _fetch_profile_row(user_id)
    completed = await _fetch_completed_slugs(user_id)
    profile = _row_profile(profile_row, email=email) if profile_row else _empty_profile(email=email)
    skills = _skills_for_resume(resume, completed)
    username = str(user.get("username") or "")

    fmt = body.format
    if fmt == "pdf":
        html_doc = render_resume_html(
            profile=profile, resume=resume, skills=skills, username=username
        )
        try:
            data = await build_pdf_bytes(html_doc)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"PDF generation unavailable: {exc}",
            ) from exc
        content_type = "application/pdf"
        ext = "pdf"
    else:
        data = build_docx_bytes(
            profile=profile, resume=resume, skills=skills, username=username
        )
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        ext = "docx"

    base_name = resume.get("versionName") or resume.get("specialization") or "resume"
    file_name = safe_filename(str(base_name), ext)
    object_key = f"{user_id}/{rid}/{uuid.uuid4().hex}.{ext}"
    storage = get_resume_storage()
    storage_ref = await storage.put_bytes(object_key, data, content_type)

    export_id = uuid.uuid4()
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_resume_exports (
                    id, user_id, resume_id, format, file_name, storage_key, expires_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP + INTERVAL '24 hours'
                )
                """,
                (
                    str(export_id),
                    user_id,
                    str(rid),
                    fmt,
                    file_name,
                    storage_ref,
                ),
            )
    finally:
        await release_db_connection(conn)

    download_url = build_api_file_url(str(export_id))
    if storage_ref.startswith("s3:"):
        presigned = storage.presign_get(storage_ref[len("s3:") :], expires_seconds=3600)
        if presigned:
            download_url = presigned

    return {
        "format": fmt,
        "fileName": file_name,
        "downloadUrl": download_url,
        "expiresAt": expires_iso(24),
        "fileId": str(export_id),
        "bytes": len(data),
    }

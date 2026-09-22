"""API формирования и доработки HH-резюме."""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from auth import require_user
from database import get_db_connection, release_db_connection
from services.resume_skills import (
    branch_completion_hints,
    generate_skills_from_progress,
    suggest_specialization,
)
from services.resume_questionnaire import (
    apply_questionnaire_to_template,
    get_questionnaire,
    validate_answers,
)

router = APIRouter(prefix="/resume", tags=["resume"])

EMPLOYMENT_ALLOWED = {"full", "part", "project", "volunteer", "internship"}
WORK_FORMAT_ALLOWED = {"office", "remote", "hybrid", "travel"}


class ResumeUpdateIn(BaseModel):
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


def _normalize_string_list(values: Optional[list[str]], allowed: set[str]) -> list[str]:
    if values is None:
        return []
    out: list[str] = []
    for raw in values:
        key = str(raw or "").strip().lower()
        if key in allowed and key not in out:
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


def _row_resume(row: tuple) -> dict[str, Any]:
    return {
        "title": str(row[1] or ""),
        "specialization": str(row[2] or ""),
        "salaryAmount": int(row[3]) if row[3] is not None else None,
        "salaryCurrency": str(row[4] or "RUB"),
        "employmentTypes": [str(x) for x in _json_list(row[5])],
        "workFormats": [str(x) for x in _json_list(row[6])],
        "about": str(row[7] or ""),
        "selectedSkillKeys": [str(x) for x in _json_list(row[8])],
        "generatedSkills": _json_list(row[9]),
        "questionnaireAnswers": _json_object(row[10]) if len(row) > 11 else {},
        "updatedAt": row[-1].isoformat() if hasattr(row[-1], "isoformat") else str(row[-1] or ""),
    }


def _empty_resume() -> dict[str, Any]:
    return {
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


async def _fetch_resume_row(user_id: int) -> Optional[tuple]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, title, specialization, salary_amount, salary_currency,
                       employment_types, work_formats, about, selected_skill_keys,
                       generated_skills, questionnaire_answers, updated_at
                FROM site_resumes
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return await cur.fetchone()
    finally:
        await release_db_connection(conn)


@router.get("")
async def get_resume(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await require_user(authorization)
    row = await _fetch_resume_row(int(user["user_id"]))
    if not row:
        return _empty_resume()
    return _row_resume(row)


@router.put("")
async def put_resume(
    body: ResumeUpdateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    existing = await _fetch_resume_row(user_id)
    cur = _row_resume(existing) if existing else _empty_resume()

    title = body.title.strip() if body.title is not None else cur["title"]
    specialization = (
        body.specialization.strip() if body.specialization is not None else cur["specialization"]
    )
    dumped = body.model_dump(exclude_unset=True)
    if "salary_amount" in dumped:
        salary_amount = dumped["salary_amount"]
    else:
        salary_amount = cur["salaryAmount"]

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
    about = body.about.strip() if body.about is not None else cur["about"]
    selected_skill_keys = (
        [str(k).strip() for k in body.selected_skill_keys if str(k).strip()]
        if body.selected_skill_keys is not None
        else cur["selectedSkillKeys"]
    )
    generated_skills = cur["generatedSkills"]

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur_db:
            await cur_db.execute(
                """
                INSERT INTO site_resumes (
                    user_id, title, specialization, salary_amount, salary_currency,
                    employment_types, work_formats, about, selected_skill_keys,
                    generated_skills, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s, %s::jsonb,
                    %s::jsonb, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    specialization = EXCLUDED.specialization,
                    salary_amount = EXCLUDED.salary_amount,
                    salary_currency = EXCLUDED.salary_currency,
                    employment_types = EXCLUDED.employment_types,
                    work_formats = EXCLUDED.work_formats,
                    about = EXCLUDED.about,
                    selected_skill_keys = EXCLUDED.selected_skill_keys,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING user_id, title, specialization, salary_amount, salary_currency,
                          employment_types, work_formats, about, selected_skill_keys,
                          generated_skills, questionnaire_answers, updated_at
                """,
                (
                    user_id,
                    title,
                    specialization,
                    salary_amount,
                    salary_currency,
                    json.dumps(employment_types, ensure_ascii=False),
                    json.dumps(work_formats, ensure_ascii=False),
                    about,
                    json.dumps(selected_skill_keys, ensure_ascii=False),
                    json.dumps(generated_skills, ensure_ascii=False),
                ),
            )
            row = await cur_db.fetchone()
    finally:
        await release_db_connection(conn)
    assert row is not None
    return _row_resume(row)


@router.post("/generate")
async def generate_resume(
    body: ResumeGenerateIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    completed = await _fetch_completed_slugs(user_id)
    selected = body.selected_skill_keys
    # None → все навыки по прогрессу Learn (обогащение).
    # list → фильтр по выбранным ключам.
    skills = generate_skills_from_progress(completed, selected_keys=selected)
    hints = branch_completion_hints(completed)
    suggested = suggest_specialization(completed)

    if body.persist:
        keys_to_store = (
            selected if selected is not None else [s["key"] for s in skills]
        )
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO site_resumes (
                        user_id, generated_skills, selected_skill_keys, updated_at
                    )
                    VALUES (%s, %s::jsonb, %s::jsonb, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        generated_skills = EXCLUDED.generated_skills,
                        selected_skill_keys = EXCLUDED.selected_skill_keys,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        user_id,
                        json.dumps(skills, ensure_ascii=False),
                        json.dumps(keys_to_store, ensure_ascii=False),
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


@router.get("/preview")
async def resume_preview(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    email = str(user.get("email") or "")
    profile_row = await _fetch_profile_row(user_id)
    resume_row = await _fetch_resume_row(user_id)
    completed = await _fetch_completed_slugs(user_id)

    profile = _row_profile(profile_row, email=email) if profile_row else _empty_profile(email=email)
    resume = _row_resume(resume_row) if resume_row else _empty_resume()

    selected = resume["selectedSkillKeys"] or None
    skills = resume["generatedSkills"]
    if not skills:
        skills = generate_skills_from_progress(completed, selected_keys=selected)
    elif selected:
        allow = set(selected)
        skills = [s for s in skills if isinstance(s, dict) and s.get("key") in allow]

    hints = branch_completion_hints(completed)
    suggested = suggest_specialization(completed)

    return {
        "profile": profile,
        "resume": resume,
        "skills": skills,
        "branchHints": hints,
        "suggestedSpecialization": suggested,
        "completedCount": len(completed),
        "username": user["username"],
    }

@router.get("/questionnaire")
async def questionnaire_schema() -> dict[str, Any]:
    return get_questionnaire()


@router.post("/questionnaire/apply")
async def questionnaire_apply(
    body: QuestionnaireApplyIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    answers = body.answers if isinstance(body.answers, dict) else {}
    errors = validate_answers(answers)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    completed = await _fetch_completed_slugs(user_id)
    hints = branch_completion_hints(completed)
    draft = apply_questionnaire_to_template(answers, branch_hints=hints)

    resume_out = {
        **_empty_resume(),
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
        existing = await _fetch_resume_row(user_id)
        prev = _row_resume(existing) if existing else _empty_resume()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO site_resumes (
                        user_id, title, specialization, salary_amount, salary_currency,
                        employment_types, work_formats, about, selected_skill_keys,
                        generated_skills, questionnaire_answers, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb, %s, %s::jsonb,
                        %s::jsonb, %s::jsonb, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        specialization = EXCLUDED.specialization,
                        salary_amount = EXCLUDED.salary_amount,
                        salary_currency = EXCLUDED.salary_currency,
                        employment_types = EXCLUDED.employment_types,
                        work_formats = EXCLUDED.work_formats,
                        about = EXCLUDED.about,
                        questionnaire_answers = EXCLUDED.questionnaire_answers,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING user_id, title, specialization, salary_amount, salary_currency,
                              employment_types, work_formats, about, selected_skill_keys,
                              generated_skills, questionnaire_answers, updated_at
                    """,
                    (
                        user_id,
                        draft["title"],
                        draft["specialization"],
                        draft["salaryAmount"],
                        draft["salaryCurrency"],
                        json.dumps(draft["employmentTypes"], ensure_ascii=False),
                        json.dumps(draft["workFormats"], ensure_ascii=False),
                        draft["about"],
                        json.dumps(prev["selectedSkillKeys"], ensure_ascii=False),
                        json.dumps(prev["generatedSkills"], ensure_ascii=False),
                        json.dumps(answers, ensure_ascii=False),
                    ),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        assert row is not None
        resume_out = _row_resume(row)

    return {
        "resume": resume_out,
        "branchHints": hints,
        "completedCount": len(completed),
        "suggestedSpecialization": draft["specialization"],
    }


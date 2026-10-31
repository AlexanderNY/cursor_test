"""CRUD портфолио и публичная страница /portfolio/p/{handle}."""
from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

import psycopg2
from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from auth import require_user
from database import get_db_connection, release_db_connection
from rate_limit import enforce_public_limit, enforce_write_limit
from services.portfolio_validate import (
    MAX_CASES,
    MAX_COVER_BYTES,
    assert_publishable,
    build_public_page,
    case_is_complete,
    cert_track_status,
    cert_track_title,
    collect_github_projects,
    display_name,
    excerpt_about,
    image_mime,
    normalize_case,
    normalize_handle,
    normalize_profile,
    quiz_pass_slugs,
    validate_reorder,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

_CASE_RETURNING = """
id::text, sort_order, title, role_label, problem, work_text, outcome,
stack, repo_url, demo_url, learn_slugs, cert_track_id, updated_at, blurb,
EXISTS (
    SELECT 1 FROM site_portfolio_covers cov
    WHERE cov.case_id = site_portfolio_cases.id
)
"""


class ProfileIn(BaseModel):
    handle: str = ""
    headline: str = ""
    summary: str = ""
    is_published: bool = False
    pinned_resume_id: Optional[str] = None
    contact_phone: str = ""
    contact_email: str = ""
    contact_url: str = ""


class CaseIn(BaseModel):
    title: str = ""
    role: str = ""
    problem: str = ""
    work: str = ""
    outcome: str = ""
    stack: list[str] = Field(default_factory=list)
    repo_url: str = ""
    demo_url: str = ""
    learn_slugs: list[str] = Field(default_factory=list)
    cert_track_id: str = ""
    blurb: str = ""


class ReorderIn(BaseModel):
    ids: list[str] = Field(default_factory=list)


def _bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


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


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _parse_case_id(raw: str) -> str:
    text = (raw or "").strip()
    try:
        return str(UUID(text))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Некорректный id кейса") from exc


async def _optional_rows(cur: Any, sql: str, params: tuple[Any, ...]) -> list[tuple]:
    try:
        await cur.execute(sql, params)
        rows = await cur.fetchall()
        return list(rows or [])
    except psycopg2.errors.UndefinedTable:
        return []


_LEARN_POSTS_SQL = """
SELECT slug, episode, title, short_title,
       EXISTS (
           SELECT 1
           FROM jsonb_array_elements(
               CASE
                   WHEN jsonb_typeof(COALESCE(structured, '{}'::jsonb)->'quiz') = 'array'
                   THEN COALESCE(structured, '{}'::jsonb)->'quiz'
                   ELSE '[]'::jsonb
               END
           ) AS question
           WHERE length(btrim(COALESCE(question->>'question', ''))) > 0
             AND length(btrim(COALESCE(question->>'answer', ''))) > 0
       ) AS has_quiz
FROM learn_posts
WHERE published_at <= NOW()
"""

_LEARN_POSTS_PLAIN_SQL = """
SELECT slug, episode, title, short_title
FROM learn_posts
WHERE published_at <= NOW()
"""


async def _learn_context(cur: Any, user_id: int) -> tuple[set[str], set[str], dict[str, dict[str, str]], list[dict[str, Any]]]:
    progress_rows = await _optional_rows(
        cur,
        "SELECT slug FROM site_learn_progress WHERE user_id = %s",
        (user_id,),
    )
    completed = {str(row[0]).strip().lower() for row in progress_rows if row and row[0]}
    post_rows = await _optional_rows(cur, _LEARN_POSTS_SQL, ())
    quiz_known = True
    if not post_rows:
        plain = await _optional_rows(cur, _LEARN_POSTS_PLAIN_SQL, ())
        if plain:
            post_rows = [(*row, False) for row in plain]
            quiz_known = False
    titles: dict[str, dict[str, str]] = {}
    posts: list[dict[str, Any]] = []
    quiz_required: set[str] = set()
    for row in post_rows:
        slug = str(row[0] or "").strip()
        item = {
            "slug": slug,
            "episode": str(row[1] or ""),
            "title": str(row[3] or row[2] or slug),
        }
        posts.append({"slug": slug, "episode": item["episode"]})
        if slug:
            titles[slug.lower()] = item
            if quiz_known and len(row) > 4 and bool(row[4]):
                quiz_required.add(slug.lower())
    attempt_rows = await _optional_rows(
        cur,
        """
        SELECT source_key, score, total
        FROM site_quiz_attempts
        WHERE user_id = %s AND source_type = 'learn'
        """,
        (user_id,),
    )
    tracks = cert_track_status(
        posts,
        completed,
        quiz_required=quiz_required if quiz_known else None,
        quiz_passed=quiz_pass_slugs(attempt_rows),
    )
    earned = {str(track["id"]) for track in tracks if track["earned"]}
    return completed, earned, titles, tracks


def _learn_refs(slugs: list[str], titles: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for slug in slugs:
        known = titles.get(slug.lower())
        if known:
            refs.append(
                {
                    "slug": known["slug"],
                    "title": known["title"],
                    "episode": known["episode"],
                }
            )
        else:
            refs.append({"slug": slug, "title": slug, "episode": ""})
    return refs


def _case_out(row: tuple, titles: dict[str, dict[str, str]]) -> dict[str, Any]:
    slugs = [str(item) for item in _json_list(row[10]) if str(item).strip()]
    track_id = str(row[11] or "")
    return {
        "id": str(row[0]),
        "sortOrder": int(row[1] or 0),
        "title": str(row[2] or ""),
        "role": str(row[3] or ""),
        "problem": str(row[4] or ""),
        "work": str(row[5] or ""),
        "outcome": str(row[6] or ""),
        "stack": [str(item) for item in _json_list(row[7])],
        "repoUrl": str(row[8] or ""),
        "demoUrl": str(row[9] or ""),
        "learnSlugs": slugs,
        "learn": _learn_refs(slugs, titles),
        "certTrackId": track_id,
        "certTrackTitle": cert_track_title(track_id),
        "updatedAt": _iso(row[12]),
        "blurb": str(row[13] or "") if len(row) > 13 else "",
        "hasCover": bool(row[14]) if len(row) > 14 else False,
    }


def _profile_out(row: tuple) -> dict[str, Any]:
    handle = str(row[1] or "")
    pinned = str(row[5]) if row[5] else None
    return {
        "handle": handle,
        "headline": str(row[2] or ""),
        "summary": str(row[3] or ""),
        "isPublished": bool(row[4]),
        "pinnedResumeId": pinned,
        "publicPath": f"/p/{handle}" if handle else "",
        "updatedAt": _iso(row[6]),
        "contactPhone": str(row[7] or "") if len(row) > 7 else "",
        "contactEmail": str(row[8] or "") if len(row) > 8 else "",
        "contactUrl": str(row[9] or "") if len(row) > 9 else "",
    }


async def _load_portfolio(cur: Any, user_id: int) -> Optional[tuple]:
    await cur.execute(
        """
        SELECT user_id, handle, headline, summary, is_published, pinned_resume_id, updated_at,
               contact_phone, contact_email, contact_url
        FROM site_portfolios
        WHERE user_id = %s
        """,
        (user_id,),
    )
    return await cur.fetchone()


async def _load_case_rows(cur: Any, user_id: int) -> list[tuple]:
    await cur.execute(
        """
        SELECT id::text, sort_order, title, role_label, problem, work_text, outcome,
               stack, repo_url, demo_url, learn_slugs, cert_track_id, updated_at, blurb,
               EXISTS (
                   SELECT 1 FROM site_portfolio_covers cov
                   WHERE cov.case_id = site_portfolio_cases.id
               )
        FROM site_portfolio_cases
        WHERE user_id = %s
        ORDER BY sort_order ASC, created_at ASC
        """,
        (user_id,),
    )
    rows = await cur.fetchall()
    return list(rows or [])


async def _identity(cur: Any, user_id: int) -> dict[str, str]:
    rows = await _optional_rows(
        cur,
        """
        SELECT u.username,
               COALESCE(p.first_name, ''),
               COALESCE(p.last_name, ''),
               COALESCE(p.city, '')
        FROM site_users u
        LEFT JOIN site_user_profiles p ON p.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    if not rows:
        return {"username": "", "first": "", "last": "", "city": ""}
    row = rows[0]
    return {
        "username": str(row[0] or ""),
        "first": str(row[1] or ""),
        "last": str(row[2] or ""),
        "city": str(row[3] or ""),
    }


async def _resume_owned(cur: Any, user_id: int, resume_id: Optional[str]) -> None:
    if not resume_id:
        return
    rows = await _optional_rows(
        cur,
        "SELECT 1 FROM site_resumes WHERE id = %s::uuid AND user_id = %s",
        (resume_id, user_id),
    )
    if not rows:
        raise HTTPException(status_code=400, detail="Закреплённое резюме не найдено")


async def _pinned_public(cur: Any, user_id: int, resume_id: Optional[str]) -> Optional[dict[str, str]]:
    if not resume_id:
        return None
    rows = await _optional_rows(
        cur,
        """
        SELECT version_name, title, specialization, about
        FROM site_resumes
        WHERE id = %s::uuid AND user_id = %s
        """,
        (resume_id, user_id),
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "versionName": str(row[0] or ""),
        "title": str(row[1] or ""),
        "specialization": str(row[2] or ""),
        "about": excerpt_about(row[3]),
    }


def _public_cases(
    rows: list[tuple],
    titles: dict[str, dict[str, str]],
    cert_codes: dict[str, str],
) -> list[dict[str, Any]]:
    public: list[dict[str, Any]] = []
    for row in rows:
        case = _case_out(row, titles)
        if not case_is_complete(case):
            continue
        public.append(
            {
                "id": case["id"],
                "title": case["title"],
                "role": case["role"],
                "problem": case["problem"],
                "work": case["work"],
                "outcome": case["outcome"],
                "stack": case["stack"],
                "repoUrl": case["repoUrl"],
                "demoUrl": case["demoUrl"],
                "learn": case["learn"],
                "certTrackTitle": case["certTrackTitle"],
                "certCode": cert_codes.get(str(case["certTrackId"]), ""),
                "blurb": str(case.get("blurb") or "").strip()
                or excerpt_about(case.get("problem"), limit=400),
                "hasCover": bool(case.get("hasCover")),
            }
        )
    return public


@router.get("/me")
async def get_mine(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            row = await _load_portfolio(cur, user_id)
            _completed, _earned, titles, _tracks = await _learn_context(cur, user_id)
            cases = [_case_out(item, titles) for item in await _load_case_rows(cur, user_id)]
    finally:
        await release_db_connection(conn)
    return {"portfolio": _profile_out(row) if row else None, "cases": cases}


@router.put("/me")
async def save_mine(
    body: ProfileIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    try:
        profile = normalize_profile(body.model_dump())
    except ValueError as exc:
        raise _bad(exc) from exc

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await _resume_owned(cur, user_id, profile["pinned_resume_id"])
            case_rows = await _load_case_rows(cur, user_id)
            _completed, _earned, titles, _tracks = await _learn_context(cur, user_id)
            cases = [_case_out(item, titles) for item in case_rows]
            if profile["is_published"]:
                try:
                    assert_publishable(headline=profile["headline"], cases=cases)
                except ValueError as exc:
                    raise _bad(exc) from exc
            try:
                await cur.execute(
                    """
                    INSERT INTO site_portfolios (
                        user_id, handle, headline, summary, is_published, pinned_resume_id,
                        contact_phone, contact_email, contact_url, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::uuid, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        handle = EXCLUDED.handle,
                        headline = EXCLUDED.headline,
                        summary = EXCLUDED.summary,
                        is_published = EXCLUDED.is_published,
                        pinned_resume_id = EXCLUDED.pinned_resume_id,
                        contact_phone = EXCLUDED.contact_phone,
                        contact_email = EXCLUDED.contact_email,
                        contact_url = EXCLUDED.contact_url,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        user_id,
                        profile["handle"],
                        profile["headline"],
                        profile["summary"],
                        profile["is_published"],
                        profile["pinned_resume_id"],
                        profile["contact_phone"],
                        profile["contact_email"],
                        profile["contact_url"],
                    ),
                )
            except psycopg2.errors.UniqueViolation as exc:
                raise HTTPException(status_code=409, detail="Этот адрес уже занят") from exc
            row = await _load_portfolio(cur, user_id)
    finally:
        await release_db_connection(conn)
    return {"portfolio": _profile_out(row) if row else None}


@router.get("/sources")
async def sources(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            identity = await _identity(cur, user_id)
            completed, _earned, titles, tracks = await _learn_context(cur, user_id)
            resume_rows = await _optional_rows(
                cur,
                """
                SELECT id::text, version_name, title, specialization, github_projects
                FROM site_resumes
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """,
                (user_id,),
            )
    finally:
        await release_db_connection(conn)

    project_lists = [_json_list(row[4]) for row in resume_rows]
    learn = []
    for slug in sorted(completed):
        known = titles.get(slug)
        learn.append(
            {
                "slug": known["slug"] if known else slug,
                "title": known["title"] if known else slug,
                "episode": known["episode"] if known else "",
            }
        )
    return {
        "displayName": display_name(identity["first"], identity["last"], identity["username"] or user["username"]),
        "githubProjects": collect_github_projects(project_lists),
        "learn": learn,
        "resumes": [
            {
                "id": str(row[0]),
                "versionName": str(row[1] or ""),
                "title": str(row[2] or ""),
                "specialization": str(row[3] or ""),
            }
            for row in resume_rows
        ],
        "certTracks": tracks,
    }


@router.post("/cases")
async def create_case(
    body: CaseIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            portfolio = await _load_portfolio(cur, user_id)
            if not portfolio:
                raise HTTPException(status_code=400, detail="Сначала сохраните адрес страницы")
            existing = await _load_case_rows(cur, user_id)
            if len(existing) >= MAX_CASES:
                raise HTTPException(status_code=400, detail=f"Не больше {MAX_CASES} кейсов")
            completed, earned, titles, _tracks = await _learn_context(cur, user_id)
            try:
                case = normalize_case(
                    body.model_dump(),
                    allowed_slugs=completed,
                    earned_ids=earned,
                )
            except ValueError as exc:
                raise _bad(exc) from exc
            if bool(portfolio[4]) and not case_is_complete(case):
                raise HTTPException(
                    status_code=400,
                    detail="Опубликованная страница принимает только материалы с названием и описанием",
                )
            next_order = max((int(row[1] or 0) for row in existing), default=-1) + 1
            await cur.execute(
                """
                INSERT INTO site_portfolio_cases (
                    user_id, sort_order, title, role_label, problem, work_text, outcome,
                    stack, repo_url, demo_url, learn_slugs, cert_track_id, blurb
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s, %s)
                RETURNING """ + _CASE_RETURNING + """
                """,
                (
                    user_id,
                    next_order,
                    case["title"],
                    case["role"],
                    case["problem"],
                    case["work"],
                    case["outcome"],
                    json.dumps(case["stack"], ensure_ascii=False),
                    case["repo_url"],
                    case["demo_url"],
                    json.dumps(case["learn_slugs"], ensure_ascii=False),
                    case["cert_track_id"],
                    case["blurb"],
                ),
            )
            created = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not created:
        raise HTTPException(status_code=500, detail="Case was not created")
    return _case_out(created, titles)


@router.put("/cases/{case_id}")
async def update_case(
    case_id: str,
    body: CaseIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    parsed_id = _parse_case_id(case_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            portfolio = await _load_portfolio(cur, user_id)
            completed, earned, titles, _tracks = await _learn_context(cur, user_id)
            try:
                case = normalize_case(
                    body.model_dump(),
                    allowed_slugs=completed,
                    earned_ids=earned,
                )
            except ValueError as exc:
                raise _bad(exc) from exc
            if portfolio and bool(portfolio[4]):
                rows = await _load_case_rows(cur, user_id)
                others = [_case_out(row, titles) for row in rows if str(row[0]) != parsed_id]
                merged = others + [case]
                try:
                    assert_publishable(headline=str(portfolio[2] or ""), cases=merged)
                except ValueError as exc:
                    raise _bad(exc) from exc
            await cur.execute(
                """
                UPDATE site_portfolio_cases
                SET title = %s,
                    role_label = %s,
                    problem = %s,
                    work_text = %s,
                    outcome = %s,
                    stack = %s::jsonb,
                    repo_url = %s,
                    demo_url = %s,
                    learn_slugs = %s::jsonb,
                    cert_track_id = %s,
                    blurb = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s::uuid AND user_id = %s
                RETURNING """ + _CASE_RETURNING + """
                """,
                (
                    case["title"],
                    case["role"],
                    case["problem"],
                    case["work"],
                    case["outcome"],
                    json.dumps(case["stack"], ensure_ascii=False),
                    case["repo_url"],
                    case["demo_url"],
                    json.dumps(case["learn_slugs"], ensure_ascii=False),
                    case["cert_track_id"],
                    case["blurb"],
                    parsed_id,
                    user_id,
                ),
            )
            updated = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not updated:
        raise HTTPException(status_code=404, detail="Кейс не найден")
    return _case_out(updated, titles)


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, bool]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    parsed_id = _parse_case_id(case_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            portfolio = await _load_portfolio(cur, user_id)
            if portfolio and bool(portfolio[4]):
                rows = await _load_case_rows(cur, user_id)
                remaining = [row for row in rows if str(row[0]) != parsed_id]
                if len(remaining) == len(rows):
                    raise HTTPException(status_code=404, detail="Кейс не найден")
                if not remaining:
                    raise HTTPException(
                        status_code=400,
                        detail="Нельзя удалить последний кейс с опубликованной страницы",
                    )
            await cur.execute(
                "DELETE FROM site_portfolio_cases WHERE id = %s::uuid AND user_id = %s",
                (parsed_id, user_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Кейс не найден")
    finally:
        await release_db_connection(conn)
    return {"ok": True}


@router.post("/cases/reorder")
async def reorder_cases(
    body: ReorderIn,
    authorization: Optional[str] = Header(None),
) -> dict[str, bool]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            rows = await _load_case_rows(cur, user_id)
            existing = [str(row[0]) for row in rows]
            try:
                requested = [_parse_case_id(item) for item in body.ids]
                validate_reorder(existing, requested)
            except ValueError as exc:
                raise _bad(exc) from exc
            for index, parsed_id in enumerate(requested):
                await cur.execute(
                    """
                    UPDATE site_portfolio_cases
                    SET sort_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s::uuid AND user_id = %s
                    """,
                    (index, parsed_id, user_id),
                )
    finally:
        await release_db_connection(conn)
    return {"ok": True}


async def _read_cover(upload: UploadFile) -> tuple[bytes, str]:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_COVER_BYTES:
            raise HTTPException(status_code=413, detail="Картинка больше 1.5 МБ")
        chunks.append(chunk)
    raw = b"".join(chunks)
    try:
        mime = image_mime(raw)
    except ValueError as exc:
        detail = str(exc)
        status = 413 if "больше" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc
    return raw, mime


def _cover_response(row: tuple) -> Response:
    payload = row[1]
    content = bytes(payload) if payload is not None else b""
    return Response(
        content=content,
        media_type=str(row[0] or "application/octet-stream"),
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post("/cases/{case_id}/cover")
async def upload_cover(
    case_id: str,
    cover: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
) -> dict[str, bool]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    parsed_id = _parse_case_id(case_id)
    raw, mime = await _read_cover(cover)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM site_portfolio_cases
                WHERE id = %s::uuid AND user_id = %s
                """,
                (parsed_id, user_id),
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="Материал не найден")
            await cur.execute(
                """
                INSERT INTO site_portfolio_covers (case_id, mime, content, updated_at)
                VALUES (%s::uuid, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (case_id) DO UPDATE SET
                    mime = EXCLUDED.mime,
                    content = EXCLUDED.content,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (parsed_id, mime, raw),
            )
    finally:
        await release_db_connection(conn)
    return {"ok": True}


@router.get("/cases/{case_id}/cover")
async def get_cover(
    case_id: str,
    authorization: Optional[str] = Header(None),
) -> Response:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    parsed_id = _parse_case_id(case_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT c.mime, c.content
                FROM site_portfolio_covers c
                JOIN site_portfolio_cases k ON k.id = c.case_id
                WHERE c.case_id = %s::uuid AND k.user_id = %s
                """,
                (parsed_id, user_id),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Картинка не найдена")
    return _cover_response(row)


@router.delete("/cases/{case_id}/cover")
async def delete_cover(
    case_id: str,
    authorization: Optional[str] = Header(None),
) -> dict[str, bool]:
    user = await require_user(authorization)
    user_id = int(user["user_id"])
    enforce_write_limit(user_id)
    parsed_id = _parse_case_id(case_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM site_portfolio_covers cov
                USING site_portfolio_cases k
                WHERE cov.case_id = k.id
                  AND cov.case_id = %s::uuid
                  AND k.user_id = %s
                """,
                (parsed_id, user_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Картинка не найдена")
    finally:
        await release_db_connection(conn)
    return {"ok": True}


@router.get("/p/{handle}/covers/{case_id}")
async def public_cover(handle: str, case_id: str, request: Request) -> Response:
    enforce_public_limit(request)
    try:
        normalized = normalize_handle(handle)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Картинка не найдена") from exc
    parsed_id = _parse_case_id(case_id)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT c.mime, c.content
                FROM site_portfolio_covers c
                JOIN site_portfolio_cases k ON k.id = c.case_id
                JOIN site_portfolios p ON p.user_id = k.user_id
                WHERE p.handle = %s
                  AND p.is_published
                  AND c.case_id = %s::uuid
                """,
                (normalized, parsed_id),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=404, detail="Картинка не найдена")
    response = _cover_response(row)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@router.get("/p/{handle}")
async def public_page(handle: str, request: Request) -> dict[str, Any]:
    enforce_public_limit(request)
    try:
        normalized = normalize_handle(handle)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Портфолио не найдено") from exc

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, handle, headline, summary, is_published, pinned_resume_id,
                       contact_phone, contact_email, contact_url
                FROM site_portfolios
                WHERE handle = %s
                """,
                (normalized,),
            )
            row = await cur.fetchone()
            if not row or not bool(row[4]):
                raise HTTPException(status_code=404, detail="Портфолио не найдено")
            user_id = int(row[0])
            identity = await _identity(cur, user_id)
            _completed, earned, titles, _tracks = await _learn_context(cur, user_id)
            code_rows = await _optional_rows(
                cur,
                "SELECT track_id, code FROM site_certificates WHERE user_id = %s",
                (user_id,),
            )
            cert_codes = {
                str(item[0]): str(item[1])
                for item in code_rows
                if item and item[0] and item[1] and str(item[0]) in earned
            }
            cases = _public_cases(await _load_case_rows(cur, user_id), titles, cert_codes)
            pinned = await _pinned_public(cur, user_id, str(row[5]) if row[5] else None)
    finally:
        await release_db_connection(conn)

    page = build_public_page(
        is_published=True,
        handle=str(row[1]),
        display=display_name(identity["first"], identity["last"], identity["username"]),
        headline=str(row[2] or ""),
        summary=str(row[3] or ""),
        city=identity["city"],
        pinned=pinned,
        cases=cases,
        contacts={
            "phone": str(row[6] or ""),
            "email": str(row[7] or ""),
            "url": str(row[8] or ""),
        },
    )
    if page is None:
        raise HTTPException(status_code=404, detail="Портфолио не найдено")
    return page

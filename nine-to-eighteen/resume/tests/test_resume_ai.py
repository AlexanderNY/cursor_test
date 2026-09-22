"""Unit tests for resume AI helpers (mocked Ollama / ai_client)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parents[1]  # resume → nine-to-eighteen → repo root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "resume_ai",
    API_DIR / "services" / "resume_ai.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_ai"] = _mod
_SPEC.loader.exec_module(_mod)

filter_skill_gap_response = _mod.filter_skill_gap_response
improve_about = _mod.improve_about
analyze_skill_gap = _mod.analyze_skill_gap
generate_cover_letter = _mod.generate_cover_letter


@pytest.fixture
def mock_ai(monkeypatch: pytest.MonkeyPatch):
    from shared import ai_client

    ready = AsyncMock(return_value=True)
    complete = AsyncMock(return_value="")
    monkeypatch.setattr(ai_client, "is_ready", ready)
    monkeypatch.setattr(ai_client, "complete", complete)
    return SimpleNamespace(is_ready=ready, complete=complete)


def test_filter_drops_unknown_skill_and_slug():
    catalog = [
        {
            "skillKey": "react",
            "name": "React",
            "missingSlugs": ["b08-react-list", "s01e10-react"],
        }
    ]
    raw = {
        "summary": "Нужен React",
        "gaps": [
            {
                "skillKey": "react",
                "learnSlugs": ["b08-react-list", "redux-toolkit-fake"],
                "reason": "для Frontend",
                "cta": "Пройдите модуль",
            },
            {
                "skillKey": "invented",
                "learnSlugs": ["x"],
                "reason": "nope",
                "cta": "",
            },
        ],
    }
    out = filter_skill_gap_response(raw, catalog)
    assert len(out["gaps"]) == 1
    assert out["gaps"][0]["skillKey"] == "react"
    assert out["gaps"][0]["learnSlugs"] == ["b08-react-list"]


@pytest.mark.asyncio
async def test_improve_about_returns_rewritten_text(mock_ai):
    mock_ai.complete.return_value = "  Профессиональный текст о Python.  "
    text = await improve_about(
        "делал пет-проекты на пайтоне",
        specialization="Middle Python Developer",
        skills=["Python — junior"],
    )
    assert "Профессиональный" in text
    mock_ai.complete.assert_awaited()


@pytest.mark.asyncio
async def test_improve_about_rejects_empty():
    with pytest.raises(ValueError):
        await improve_about("  ")


@pytest.mark.asyncio
async def test_analyze_skill_gap_filters_hallucinations(mock_ai):
    mock_ai.complete.return_value = (
        '{"summary":"ok","gaps":[{"skillKey":"python","learnSlugs":["b03-python","fake"],'
        '"reason":"r","cta":"c"}]}'
    )
    catalog = [
        {
            "skillKey": "python",
            "name": "Python",
            "missingSlugs": ["b03-python", "b07-notes-api"],
        }
    ]
    result = await analyze_skill_gap(
        target_role="Backend",
        selected_skills=["Docker"],
        completed_slugs=[],
        catalog=catalog,
    )
    assert result["targetRole"] == "Backend"
    assert result["gaps"][0]["learnSlugs"] == ["b03-python"]


@pytest.mark.asyncio
async def test_analyze_skill_gap_empty_catalog_no_llm(mock_ai):
    result = await analyze_skill_gap(
        target_role="QA",
        selected_skills=[],
        completed_slugs=["map-qa"],
        catalog=[],
    )
    assert result["gaps"] == []
    assert "нет" in result["summary"].lower()
    mock_ai.complete.assert_not_awaited()


@pytest.mark.asyncio
async def test_cover_letter_not_empty(mock_ai):
    mock_ai.complete.return_value = "Уважаемый работодатель,\n\nТекст письма."
    letter = await generate_cover_letter(
        resume_ctx={"fullName": "Иван", "skills": ["Python"]},
        vacancy_text="Ищем Python-разработчика с опытом FastAPI и PostgreSQL.",
    )
    assert "Уважаемый" in letter


@pytest.mark.asyncio
async def test_ai_unavailable_raises(monkeypatch: pytest.MonkeyPatch):
    from shared import ai_client

    monkeypatch.setattr(ai_client, "is_ready", AsyncMock(return_value=False))
    with pytest.raises(RuntimeError, match="недоступен"):
        await improve_about("текст", specialization="Dev")


@pytest.mark.asyncio
async def test_mock_interview_parses_questions(mock_ai):
    mock_ai.complete.return_value = (
        '{"questions":[{"id":"q1","skillKey":"python","question":"Что такое GIL?",'
        '"hint":"threading"},{"id":"q2","skillKey":"fake","question":"Redux?",'
        '"hint":""}]}'
    )
    qs = await _mod.generate_mock_interview(
        specialization="Python",
        skills=[{"key": "python", "name": "Python", "display": "Python — middle"}],
    )
    assert len(qs) >= 1
    assert qs[0]["question"]
    assert all(q["skillKey"] in ("python", "") or q["skillKey"] == "python" for q in qs)

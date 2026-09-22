"""Unit tests for resume questionnaire template fill."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "resume_questionnaire",
    API_DIR / "services" / "resume_questionnaire.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_questionnaire"] = _mod
_SPEC.loader.exec_module(_mod)

apply_questionnaire_to_template = _mod.apply_questionnaire_to_template
get_questionnaire = _mod.get_questionnaire
validate_answers = _mod.validate_answers


def _valid_answers(**overrides):
    base = {
        "role_track": "devops",
        "experience_level": "junior",
        "goal": "first_job",
        "employment": ["full", "internship"],
        "work_formats": ["remote", "hybrid"],
        "salary_band": "120_180",
        "strengths": ["learning", "ops", "pet"],
        "tone": "balanced",
        "extra": "Готов к менторству.",
    }
    base.update(overrides)
    return base


def test_questionnaire_has_required_questions():
    data = get_questionnaire()
    ids = [q["id"] for q in data["questions"]]
    assert "role_track" in ids
    assert "strengths" in ids
    assert data["version"] == 1


def test_validate_requires_multi_fields():
    bad = _valid_answers(employment=[])
    errors = validate_answers(bad)
    assert errors


def test_apply_fills_specialization_and_salary():
    draft = apply_questionnaire_to_template(_valid_answers())
    assert "DevOps" in draft["specialization"]
    assert draft["salaryAmount"] == 150_000
    assert "full" in draft["employmentTypes"]
    assert "remote" in draft["workFormats"]
    assert "менторству" in draft["about"]
    assert "учусь" in draft["about"].lower() or "учебн" in draft["about"].lower()


def test_concise_tone_is_shorter_than_detailed():
    concise = apply_questionnaire_to_template(_valid_answers(tone="concise", extra=""))
    detailed = apply_questionnaire_to_template(
        _valid_answers(tone="detailed", extra=""),
        branch_hints=["ветка карты: Devops"],
    )
    assert len(detailed["about"]) > len(concise["about"])

"""Unit tests for resume strength score."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
# Load resume_skills first (dependency)
_skills_spec = importlib.util.spec_from_file_location(
    "resume_skills",
    API_DIR / "services" / "resume_skills.py",
)
assert _skills_spec and _skills_spec.loader
_skills = importlib.util.module_from_spec(_skills_spec)
sys.modules["services.resume_skills"] = _skills
sys.modules["resume_skills"] = _skills
_skills_spec.loader.exec_module(_skills)

# Fake package path for `from services.resume_skills import ...`
import types

services_pkg = types.ModuleType("services")
services_pkg.resume_skills = _skills
sys.modules["services"] = services_pkg

_SPEC = importlib.util.spec_from_file_location(
    "resume_strength",
    API_DIR / "services" / "resume_strength.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_strength"] = _mod
_SPEC.loader.exec_module(_mod)

compute_resume_strength = _mod.compute_resume_strength
PHOTO_POINTS = _mod.PHOTO_POINTS
ABOUT_POINTS = _mod.ABOUT_POINTS
LEARN_POINTS_PER_MODULE = _mod.LEARN_POINTS_PER_MODULE


def test_empty_resume_score_zero_with_actions():
    result = compute_resume_strength(has_photo=False, about="", completed_slugs=[])
    assert result["score"] == 0
    ids = {a["id"] for a in result["actions"]}
    assert "photo" in ids
    assert "about" in ids


def test_photo_and_about_points():
    result = compute_resume_strength(
        has_photo=True,
        about="x" * 50,
        completed_slugs=[],
    )
    assert result["score"] == PHOTO_POINTS + ABOUT_POINTS
    assert all(a["id"] not in ("photo", "about") for a in result["actions"])


def test_learn_module_points_and_cap():
    # Many docker-related + other slugs → score capped at 100
    slugs = [
        "b10-docker",
        "b11-compose",
        "b03-python",
        "b07-notes-api",
        "s01e05-fastapi",
        "s01e07-postgres",
        "s01e08-sql",
        "map-redis",
        "s01e03-git",
        "b02-git",
    ]
    result = compute_resume_strength(
        has_photo=True,
        about="x" * 50,
        specialization="Backend / Fullstack-разработчик",
        completed_slugs=slugs,
    )
    assert result["score"] <= 100
    assert result["score"] >= PHOTO_POINTS + ABOUT_POINTS + LEARN_POINTS_PER_MODULE


def test_action_links_to_learn_slug():
    result = compute_resume_strength(
        has_photo=True,
        about="x" * 50,
        specialization="DevOps",
        completed_slugs=[],
    )
    learn_actions = [a for a in result["actions"] if str(a["id"]).startswith("learn:")]
    assert learn_actions
    assert learn_actions[0]["href"].startswith("/game/learn/")

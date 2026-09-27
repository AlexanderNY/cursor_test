"""Unit tests for vacancy Match Score."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def _load(name: str, relative: str) -> ModuleType:
    path = API_DIR / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_sanitize = _load("text_sanitize", "services/text_sanitize.py")
_skills = _load("resume_skills", "services/resume_skills.py")
sys.modules["services.text_sanitize"] = _sanitize
sys.modules["services.resume_skills"] = _skills

services_pkg = ModuleType("services")
services_pkg.__path__ = [str(API_DIR / "services")]  # type: ignore[attr-defined]
services_pkg.text_sanitize = _sanitize
services_pkg.resume_skills = _skills
sys.modules["services"] = services_pkg

_src = _load("resume_source", "services/resume_source.py")
sys.modules["services.resume_source"] = _src

_match = _load("resume_match", "services/resume_match.py")
sys.modules["services.resume_match"] = _match

compute_match_score = _match.compute_match_score


def test_match_full_overlap():
    result = compute_match_score(
        vacancy_text="Ищем Python-разработчика с FastAPI и PostgreSQL.",
        selected_keys=["python", "fastapi", "postgresql"],
        generated_skills=[],
    )
    assert result["score"] == 100
    assert set(result["matchedKeys"]) == {"python", "fastapi", "postgresql"}
    assert result["missingKeys"] == []


def test_match_partial_and_clamp():
    result = compute_match_score(
        vacancy_text="Нужен Python, FastAPI, Docker и Kubernetes.",
        selected_keys=["python"],
        generated_skills=[{"key": "fastapi", "name": "FastAPI"}],
        about="",
        source_text="",
    )
    assert 0 <= result["score"] <= 100
    assert "python" in result["matchedKeys"]
    assert "fastapi" in result["matchedKeys"]
    assert "docker" in result["missingKeys"]
    assert "kubernetes" in result["missingKeys"]
    assert result["score"] == 50


def test_match_no_known_tokens():
    result = compute_match_score(
        vacancy_text="Ищем доброго человека в дружный коллектив без технологий.",
        selected_keys=["python"],
        generated_skills=[],
    )
    assert result["requiredKeys"] == []
    assert result["score"] == 50
    assert "python" in result["matchedKeys"]


def test_match_empty_resume_no_tokens():
    result = compute_match_score(
        vacancy_text="просто текст без стека",
        selected_keys=[],
        generated_skills=[],
    )
    assert result["score"] == 0

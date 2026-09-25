"""Unit tests for DOCX/HTML export builders (no browser required)."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]

_sanitize_spec = importlib.util.spec_from_file_location(
    "text_sanitize",
    API_DIR / "services" / "text_sanitize.py",
)
assert _sanitize_spec and _sanitize_spec.loader
_sanitize = importlib.util.module_from_spec(_sanitize_spec)
sys.modules["text_sanitize"] = _sanitize
_sanitize_spec.loader.exec_module(_sanitize)

services_pkg = types.ModuleType("services")
services_pkg.text_sanitize = _sanitize
sys.modules["services"] = services_pkg
sys.modules["services.text_sanitize"] = _sanitize

_SPEC = importlib.util.spec_from_file_location(
    "resume_export",
    API_DIR / "services" / "resume_export.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_export"] = _mod
_SPEC.loader.exec_module(_mod)

build_docx_bytes = _mod.build_docx_bytes
render_resume_html = _mod.render_resume_html


PROFILE = {
    "lastName": "Иванов",
    "firstName": "Иван",
    "patronymic": "",
    "phone": "+7000",
    "email": "a@b.c",
    "city": "Москва",
    "birthDate": "1990-01-01",
    "citizenship": "РФ",
    "readyForTrips": True,
}

RESUME = {
    "versionName": "Python Backend",
    "title": "Backend",
    "specialization": "Backend-разработчик (Python)",
    "salaryAmount": 150000,
    "salaryCurrency": "RUB",
    "employmentTypes": ["full"],
    "workFormats": ["remote"],
    "about": "Учусь на 9to18.",
}

SKILLS = [{"key": "python", "name": "Python", "display": "Python — junior"}]


def test_render_html_contains_specialization():
    html_doc = render_resume_html(
        profile=PROFILE, resume=RESUME, skills=SKILLS, username="ivan"
    )
    assert "Backend-разработчик" in html_doc
    assert "Иванов" in html_doc
    assert "Python — junior" in html_doc


def test_render_html_escapes_script_in_about():
    dirty = {
        **RESUME,
        "about": '<script>alert(1)</script>Опыт Python',
    }
    html_doc = render_resume_html(
        profile=PROFILE, resume=dirty, skills=SKILLS, username="ivan"
    )
    assert "<script>" not in html_doc
    assert "alert(1)" in html_doc
    assert "Опыт Python" in html_doc


def test_docx_bytes_non_empty():
    data = build_docx_bytes(
        profile=PROFILE, resume=RESUME, skills=SKILLS, username="ivan"
    )
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 1000
    assert data[:2] == b"PK"

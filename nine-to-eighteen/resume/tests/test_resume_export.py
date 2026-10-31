"""Unit tests for DOCX/HTML export builders (no browser required)."""
from __future__ import annotations

import importlib.util
import sys
import types
from io import BytesIO
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
services_pkg.__path__ = [str(API_DIR / "services")]  # type: ignore[attr-defined]
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
normalize_education = _mod.normalize_education
normalize_experience = _mod.normalize_experience
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
    "experience": [
        {
            "company": "ООО Ромашка",
            "position": "Разработчик",
            "city": "Москва",
            "start": "2020-01",
            "end": "",
            "description": "Писал API",
        }
    ],
    "education": [
        {
            "level": "higher",
            "institution": "МГУ",
            "faculty": "ВМК",
            "specialty": "Прикладная математика",
            "year": 2018,
        }
    ],
}

SKILLS = [{"key": "python", "name": "Python", "display": "Python — junior"}]


def test_render_html_contains_specialization():
    html_doc = render_resume_html(
        profile=PROFILE, resume=RESUME, skills=SKILLS, username="ivan"
    )
    assert "Backend-разработчик" in html_doc
    assert "Иванов" in html_doc
    assert "Python" in html_doc
    assert "Желаемая должность и зарплата" in html_doc
    assert "Опыт работы" in html_doc
    assert "Январь 2020 — настоящее время" in html_doc
    assert "Образование" in html_doc
    assert "Обо мне" in html_doc
    assert "<script>" not in html_doc


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


def _docx_text(data: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def test_docx_bytes_non_empty():
    data = build_docx_bytes(
        profile=PROFILE, resume=RESUME, skills=SKILLS, username="ivan"
    )
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 1000
    assert data[:2] == b"PK"


def test_docx_uses_hh_section_headings():
    data = build_docx_bytes(
        profile=PROFILE, resume=RESUME, skills=SKILLS, username="ivan"
    )
    text = _docx_text(data)
    assert "Телефон: +7000" in text
    assert "Дата рождения: 1 января 1990" in text
    assert "Желаемая должность и зарплата" in text
    assert "150 000 руб." in text
    assert "Занятость: полная занятость" in text
    assert "График работы: удаленная работа" in text
    assert "Опыт работы" in text
    assert "Январь 2020 — настоящее время" in text
    assert "ООО Ромашка" in text
    assert "Образование" in text
    assert "Высшее" in text
    assert "МГУ" in text
    assert "Ключевые навыки" in text
    assert "Python" in text
    assert "Обо мне" in text
    assert "Учусь на 9to18." in text


def test_normalize_experience_drops_incomplete_and_orders_dates():
    items = normalize_experience(
        [
            {"company": "", "position": "Dev", "start": "2020-01"},
            {
                "company": "Studio",
                "position": "QA",
                "start": "2022-05",
                "end": "2021-03",
                "description": "  тесты  ",
            },
        ]
    )
    assert len(items) == 1
    assert items[0]["start"] == "2021-03"
    assert items[0]["end"] == "2022-05"
    assert items[0]["description"] == "тесты"


def test_normalize_education_keeps_known_level():
    items = normalize_education(
        [
            {"institution": "", "level": "higher"},
            {"institution": "Колледж", "level": "nope", "year": 2010},
        ]
    )
    assert len(items) == 1
    assert items[0]["institution"] == "Колледж"
    assert items[0]["level"] == ""
    assert items[0]["year"] == 2010

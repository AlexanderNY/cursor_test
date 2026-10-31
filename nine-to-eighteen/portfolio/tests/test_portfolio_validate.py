"""Unit tests for portfolio validation (no database)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "portfolio_validate_ut",
        API_DIR / "services" / "portfolio_validate.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["portfolio_validate_ut"] = module
    spec.loader.exec_module(module)
    return module


v = _load()


def test_handle_normalizes_and_rejects_reserved():
    assert v.normalize_handle("  Ivan-Dev ") == "ivan-dev"
    try:
        v.normalize_handle("me")
    except ValueError as exc:
        assert "зарезервирован" in str(exc)
    else:
        raise AssertionError("reserved handle must fail")
    try:
        v.normalize_handle("ab")
    except ValueError:
        return
    raise AssertionError("short handle must fail")


def test_case_rejects_unfinished_learn_and_bad_url():
    try:
        v.normalize_case(
            {"title": "Notes", "learn_slugs": ["b02-git"]},
            allowed_slugs=set(),
            earned_ids=set(),
        )
    except ValueError as exc:
        assert "Learn" in str(exc)
    else:
        raise AssertionError("unknown learn slug must fail")

    try:
        v.normalize_case(
            {"title": "Notes", "repo_url": "javascript:alert(1)"},
            allowed_slugs=set(),
            earned_ids=set(),
        )
    except ValueError as exc:
        assert "http" in str(exc)
    else:
        raise AssertionError("bad url must fail")

    case = v.normalize_case(
        {
            "title": "<b>Notes</b>",
            "role": "backend",
            "problem": "форма теряла заявки",
            "work": "добавил API",
            "outcome": "заявки сохраняются",
            "stack": ["FastAPI", "fastapi", "Postgres"],
            "repo_url": "https://github.com/example/notes",
            "learn_slugs": ["b02-git"],
        },
        allowed_slugs={"b02-git"},
        earned_ids=set(),
    )
    assert case["title"] == "Notes"
    assert case["stack"] == ["FastAPI", "Postgres"]
    assert case["repo_url"].startswith("https://")


def test_blurb_and_contacts_and_image_mime():
    case = v.normalize_case(
        {"title": "Макет", "blurb": "<i>лендинг</i> студии", "demo_url": "https://example.com"},
        allowed_slugs=set(),
        earned_ids=set(),
    )
    assert case["blurb"] == "лендинг студии"
    v.assert_publishable(headline="Портфолио", cases=[case])
    profile = v.normalize_profile(
        {
            "handle": "ivan-dev",
            "contact_phone": " +7 900 000-00-00 ",
            "contact_email": "a@b.co",
            "contact_url": "https://t.me/ivan",
        }
    )
    assert profile["contact_email"] == "a@b.co"
    assert profile["contact_url"].startswith("https://")
    try:
        v.normalize_profile({"handle": "ivan-dev", "contact_email": "not-an-email"})
    except ValueError as exc:
        assert "email" in str(exc).lower()
    else:
        raise AssertionError("bad email must fail")
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    assert v.image_mime(png) == "image/png"
    try:
        v.image_mime(b"<html>not-an-image</html>")
    except ValueError as exc:
        assert "картин" in str(exc)
    else:
        raise AssertionError("html must not pass as an image")


def test_publish_requires_complete_cases():
    try:
        v.assert_publishable(
            headline="Портфолио",
            cases=[{"title": "Черновик", "problem": "", "work": "", "outcome": ""}],
        )
    except ValueError as exc:
        assert "Черновик" in str(exc)
    else:
        raise AssertionError("incomplete case must block publish")
    v.assert_publishable(
        headline="Портфолио",
        cases=[
            {
                "title": "Notes",
                "problem": "задача",
                "work": "сделал",
                "outcome": "результат",
            }
        ],
    )


def test_cert_track_earned_only_when_every_episode_done():
    posts = [
        {"slug": "b01-karta", "episode": "B01"},
        {"slug": "b02-git", "episode": "B02"},
        {"slug": "py01-types", "episode": "PY01"},
    ]
    partial = v.cert_track_status(posts, {"b01-karta"})
    by_id = {item["id"]: item for item in partial}
    assert by_id["b"]["earned"] is False
    assert by_id["b"]["done"] == 1
    assert by_id["py"]["earned"] is False
    full = v.cert_track_status(posts, {"b01-karta", "b02-git", "py01-types"})
    earned = {item["id"] for item in full if item["earned"]}
    assert earned == {"b", "py"}
    gated = v.cert_track_status(
        posts,
        {"b01-karta", "b02-git", "py01-types"},
        quiz_required={"py01-types"},
        quiz_passed=set(),
    )
    assert {item["id"] for item in gated if item["earned"]} == {"b"}
    opened = v.cert_track_status(
        posts,
        {"b01-karta", "b02-git", "py01-types"},
        quiz_required={"py01-types"},
        quiz_passed=v.quiz_pass_slugs([("learn/py01-types", 7, 10)]),
    )
    assert {item["id"] for item in opened if item["earned"]} == {"b", "py"}


def test_github_dedupes_and_prefers_selected():
    projects = v.collect_github_projects(
        [
            [
                {"name": "notes", "url": "https://github.com/a/notes", "selected": False, "language": "Python"},
                {"name": "fork-skip", "url": "not a url"},
            ],
            [
                {"name": "notes", "url": "https://github.com/a/notes", "selected": True, "language": "Python"},
                {"name": "other", "url": "https://github.com/a/other", "selected": False},
            ],
        ]
    )
    assert projects[0]["name"] == "notes"
    assert projects[0]["selected"] is True
    assert [item["name"] for item in projects] == ["notes", "other"]


def test_public_page_hides_unpublished_and_keeps_case_story():
    assert (
        v.build_public_page(
            is_published=False,
            handle="ivan",
            display="Иван",
            headline="backend",
            summary="",
            city="",
            pinned=None,
            cases=[],
        )
        is None
    )
    page = v.build_public_page(
        is_published=True,
        handle="ivan",
        display="Иван Петров",
        headline="Backend",
        summary="Кейсы с курса",
        city="Казань",
        pinned={"title": "Python", "about": "x" * 700},
        cases=[{"title": "Notes", "problem": "a", "work": "b", "outcome": "c"}],
    )
    assert page is not None
    assert page["displayName"] == "Иван Петров"
    assert "email" not in page
    assert page["cases"][0]["outcome"] == "c"
    assert v.excerpt_about("x" * 700).endswith("…")
    assert len(v.excerpt_about("x" * 700)) == v.ABOUT_EXCERPT


def test_reorder_requires_the_same_ids():
    v.validate_reorder(["a", "b"], ["b", "a"])
    try:
        v.validate_reorder(["a", "b"], ["a"])
    except ValueError:
        return
    raise AssertionError("partial reorder must fail")

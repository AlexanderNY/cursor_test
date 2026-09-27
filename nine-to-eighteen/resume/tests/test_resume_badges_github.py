"""Unit tests for resume badges and GitHub helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, API_DIR / relative)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_badges = _load("resume_badges_ut", "services/resume_badges.py")
_github = _load("resume_github_ut", "services/resume_github.py")

compute_badges = _badges.compute_badges
filter_selected_badge_ids = _badges.filter_selected_badge_ids
is_quiz_passed = _badges.is_quiz_passed
learn_season_required_slugs = _badges.learn_season_required_slugs

parse_repo_payload = _github.parse_repo_payload
filter_selected_projects = _github.filter_selected_projects
selected_projects_only = _github.selected_projects_only
normalize_github_username = _github.normalize_github_username


def test_learn_badge_earned_when_all_slugs_done():
    required = learn_season_required_slugs("learn_season_b")
    assert len(required) >= 1
    badges = compute_badges(completed_slugs=list(required), quiz_attempts=[])
    season = next(b for b in badges if b["id"] == "learn_season_b")
    assert season["earned"] is True
    assert season["progress"]["done"] == season["progress"]["total"]


def test_learn_badge_not_earned_partial():
    required = learn_season_required_slugs("learn_season_b")
    partial = list(required)[:1] if required else []
    badges = compute_badges(completed_slugs=partial, quiz_attempts=[])
    season = next(b for b in badges if b["id"] == "learn_season_b")
    if len(required) > 1:
        assert season["earned"] is False


def test_quiz_pass_and_count_badges():
    attempts = [
        {"source_key": "learn/ep1", "score": 8, "total": 10},
        {"source_key": "learn/ep2", "score": 2, "total": 10},
        {"source_key": "learn/ep3", "score": 9, "total": 10},
        {"source_key": "learn/ep4", "score": 7, "total": 10},
    ]
    assert is_quiz_passed(8, 10) is True
    assert is_quiz_passed(2, 10) is False
    assert is_quiz_passed(7, 2) is False  # total < 3

    badges = compute_badges(completed_slugs=[], quiz_attempts=attempts)
    by_id = {b["id"]: b for b in badges}
    assert by_id["quiz_count_1"]["earned"] is True
    assert by_id["quiz_count_3"]["earned"] is True
    assert by_id["quiz_count_5"]["earned"] is False
    assert any(b["id"].startswith("quiz_src_") and b["earned"] for b in badges)


def test_filter_selected_badge_ids():
    out = filter_selected_badge_ids(
        ["quiz_count_1", "fake", "quiz_count_1", "learn_season_b"],
        earned_ids={"quiz_count_1", "learn_season_b"},
        max_count=8,
    )
    assert out == ["quiz_count_1", "learn_season_b"]


def test_parse_github_repos_skips_forks():
    items = [
        {
            "name": "notes",
            "html_url": "https://github.com/u/notes",
            "description": "app",
            "language": "Python",
            "stargazers_count": 3,
            "fork": False,
        },
        {
            "name": "forked",
            "html_url": "https://github.com/u/forked",
            "fork": True,
            "stargazers_count": 99,
        },
    ]
    parsed = parse_repo_payload(items)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "notes"
    assert parsed[0]["stars"] == 3
    assert parsed[0]["selected"] is False


def test_selected_projects_cap():
    projects = [
        {
            "name": f"r{i}",
            "url": f"https://github.com/u/r{i}",
            "description": "",
            "language": "Go",
            "stars": i,
            "selected": True,
        }
        for i in range(10)
    ]
    filtered = filter_selected_projects(projects, max_count=6)
    assert sum(1 for p in filtered if p["selected"]) == 6
    assert len(selected_projects_only(filtered)) == 6


def test_normalize_github_username():
    assert normalize_github_username("@Octocat") == "Octocat"
    try:
        normalize_github_username("-bad")
        assert False, "expected ValueError"
    except ValueError:
        pass

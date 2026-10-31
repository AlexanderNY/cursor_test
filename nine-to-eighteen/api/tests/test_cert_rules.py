"""Правила сертификата без базы."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "cert_rules_ut",
        API_DIR / "services" / "cert_rules.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["cert_rules_ut"] = module
    spec.loader.exec_module(module)
    return module


rules = _load()


def test_has_quiz_needs_question_and_answer():
    assert rules.has_quiz({"quiz": [{"question": "Q", "answer": "A"}]}) is True
    assert rules.has_quiz({"quiz": [{"question": "Q", "answer": ""}]}) is False
    assert rules.has_quiz({}) is False


def test_certificate_holder_name_uses_last_and_first():
    assert (
        rules.certificate_holder_name("Иванов", "Иван", "Иванович", "ivan")
        == "Иванов Иван Иванович"
    )
    assert rules.certificate_holder_name("Иванов", "", "", "ivan") == "Иванов"
    assert rules.certificate_holder_name("", "", "", "ivan") == "ivan"
    assert rules.certificate_holder_name("", "", "", "  ") == "Участник"


def test_blank_code_is_stable_and_shaped():
    code = rules.blank_code(7, "py")
    assert code == rules.blank_code(7, "py")
    assert code != rules.blank_code(8, "py")
    assert rules.is_cert_code(code) is True
    assert rules.is_cert_code("nope") is False


def test_track_not_earned_until_quiz_hits_threshold():
    posts = [
        {"slug": "py-intro", "episode": "PY01", "has_quiz": True},
        {"slug": "py-types", "episode": "PY02", "has_quiz": False},
    ]
    attempts = [{"source_key": "learn/py-intro", "score": 1, "total": 2}]
    low = rules.assess_tracks(posts, {"py-intro", "py-types"}, rules.best_quiz_percents(attempts))
    assert low[0]["id"] == "py"
    assert low[0]["earned"] is False
    assert low[0]["quiz_missing"] == ["py-intro"]

    passed = rules.assess_tracks(
        posts,
        {"py-intro", "py-types"},
        rules.best_quiz_percents([{"source_key": "learn/py-intro", "score": 7, "total": 10}]),
    )
    assert passed[0]["earned"] is True
    assert passed[0]["quiz_percent"] == 70


def test_track_without_quiz_earns_on_episodes_only():
    posts = [{"slug": "b01", "episode": "B01", "has_quiz": False}]
    board = rules.assess_tracks(posts, {"b01"}, {})
    assert board[0]["earned"] is True
    assert board[0]["quiz_required"] == 0


def test_best_attempt_wins():
    best = rules.best_quiz_percents(
        [
            {"source_key": "learn/py-intro", "score": 1, "total": 4},
            {"source_key": "learn/py-intro", "score": 3, "total": 4},
            {"source_key": "blog/other", "score": 4, "total": 4},
        ]
    )
    assert best == {"py-intro": 75}


def test_interview_track_needs_perfect_score_and_min_total():
    short = rules.assess_interview_track(
        [{"source_key": "learn/interview", "score": 5, "total": 5}]
    )
    assert short["id"] == "interview"
    assert short["earned"] is False
    assert short["quiz_percent"] == 0

    low = rules.assess_interview_track(
        [{"source_key": "learn/interview/python", "score": 9, "total": 10}]
    )
    assert low["earned"] is False
    assert low["quiz_percent"] == 90

    perfect = rules.assess_interview_track(
        [
            {"source_key": "learn/interview/python", "score": 9, "total": 10},
            {"source_key": "learn/interview", "score": 10, "total": 10},
            {"source_key": "learn/py-intro", "score": 10, "total": 10},
        ]
    )
    assert perfect["earned"] is True
    assert perfect["quiz_percent"] == 100
    assert perfect["done"] == 1
    assert perfect["total"] == 1
    assert rules.is_cert_code(rules.blank_code(3, "interview")) is True

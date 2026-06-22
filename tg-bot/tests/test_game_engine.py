"""Unit-тесты игрового движка."""

from __future__ import annotations

from unittest.mock import patch

from services.game_engine import PickQuestionsInput, pick_random_questions, score_for_answer


def test_pick_random_questions_respects_limit() -> None:
    params = PickQuestionsInput(
        question_ids=[10, 20, 30, 40, 50],
        questions_per_game=3,
    )
    with patch("services.game_engine.random.shuffle", lambda x: None):
        out = pick_random_questions(params)
    assert len(out.selected_ids) == 3
    assert set(out.selected_ids).issubset({10, 20, 30, 40, 50})


def test_pick_random_questions_empty_pool() -> None:
    out = pick_random_questions(
        PickQuestionsInput(question_ids=[], questions_per_game=5)
    )
    assert out.selected_ids == []


def test_pick_random_questions_pool_smaller_than_limit() -> None:
    params = PickQuestionsInput(question_ids=[1, 2], questions_per_game=10)
    with patch("services.game_engine.random.shuffle", lambda x: None):
        out = pick_random_questions(params)
    assert len(out.selected_ids) == 2


def test_score_for_answer() -> None:
    assert score_for_answer(was_correct=True) == 1
    assert score_for_answer(was_correct=False) == 0
    assert score_for_answer(was_correct=True, points=5) == 5

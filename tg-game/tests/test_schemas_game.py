"""Валидация Pydantic-схем игры."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas_game import GameOptionInput, GameQuestionCreate


def _six_options(correct_index: int = 2) -> list[GameOptionInput]:
    opts = []
    for i in range(1, 7):
        opts.append(
            GameOptionInput(
                option_index=i,
                option_text=f"Answer {i}",
                is_correct=(i == correct_index),
            )
        )
    return opts


def test_game_question_create_valid() -> None:
    body = GameQuestionCreate(
        mode_id=1,
        prompt_text="What?",
        options=_six_options(3),
    )
    assert len(body.options) == 6


def test_game_question_create_wrong_option_count() -> None:
    with pytest.raises(ValidationError):
        GameQuestionCreate(
            mode_id=1,
            prompt_text="What?",
            options=_six_options()[:5],
        )


def test_game_question_create_two_correct() -> None:
    opts = _six_options(2)
    opts[0] = GameOptionInput(option_index=1, option_text="also correct", is_correct=True)
    with pytest.raises(ValidationError):
        GameQuestionCreate(mode_id=1, prompt_text="What?", options=opts)


def test_game_question_create_no_correct() -> None:
    opts = [
        GameOptionInput(option_index=i, option_text=str(i), is_correct=False)
        for i in range(1, 7)
    ]
    with pytest.raises(ValidationError):
        GameQuestionCreate(mode_id=1, prompt_text="What?", options=opts)

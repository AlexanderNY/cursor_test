"""Чистая логика игры (без I/O): выбор вопросов, подсчёт очков."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class PickQuestionsInput:
    """RORO: вход для выбора вопросов."""

    question_ids: Sequence[int]
    questions_per_game: int


@dataclass(frozen=True, slots=True)
class PickQuestionsOutput:
    """RORO: результат выбора вопросов."""

    selected_ids: list[int]


def pick_random_questions(params: PickQuestionsInput) -> PickQuestionsOutput:
    """Перемешивает и обрезает список id вопросов до лимита режима."""
    if params.questions_per_game <= 0:
        return PickQuestionsOutput(selected_ids=[])

    pool = list(dict.fromkeys(params.question_ids))  # уникальные, порядок сохранён
    if not pool:
        return PickQuestionsOutput(selected_ids=[])

    random.shuffle(pool)
    take = min(len(pool), params.questions_per_game)
    return PickQuestionsOutput(selected_ids=pool[:take])


def score_for_answer(*, was_correct: bool, points: int = 1) -> int:
    """Очки за один ответ (расширяемо: множители, сложность)."""
    return points if was_correct else 0

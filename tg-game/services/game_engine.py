"""Чистая логика игры (без I/O): выбор вопросов, подсчёт очков."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence, TypeVar

T = TypeVar("T")


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


def shuffle_for_display(items: Sequence[T]) -> list[T]:
    """Случайный порядок элементов при показе (новая копия списка)."""
    pool = list(items)
    random.shuffle(pool)
    return pool


def score_for_answer(*, was_correct: bool, points: int = 1) -> int:
    """Очки за один ответ (расширяемо: множители, сложность)."""
    return points if was_correct else 0


@dataclass(frozen=True, slots=True)
class CountryQuizRound:
    """Один шаг викторины по странам: верная страна и 6 вариантов."""

    country_id: int
    option_country_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BuildCountryQuizInput:
    country_ids: Sequence[int]
    questions_per_game: int = 10
    options_per_question: int = 6


@dataclass(frozen=True, slots=True)
class BuildCountryQuizOutput:
    rounds: tuple[CountryQuizRound, ...]


def build_country_quiz_rounds(params: BuildCountryQuizInput) -> BuildCountryQuizOutput:
    """
    Собирает партию: N разных стран, у каждой ровно K уникальных вариантов,
    верная страна всегда среди вариантов.
    """
    pool = list(dict.fromkeys(params.country_ids))
    if (
        params.questions_per_game <= 0
        or params.options_per_question <= 0
        or len(pool) < params.options_per_question
    ):
        return BuildCountryQuizOutput(rounds=())

    random.shuffle(pool)
    take = min(len(pool), params.questions_per_game)
    selected = pool[:take]
    remaining = pool[take:]

    rounds: list[CountryQuizRound] = []
    for correct_id in selected:
        distractor_pool = [cid for cid in remaining + selected if cid != correct_id]
        random.shuffle(distractor_pool)
        need = params.options_per_question - 1
        if len(distractor_pool) < need:
            return BuildCountryQuizOutput(rounds=())
        option_ids = [correct_id, *distractor_pool[:need]]
        random.shuffle(option_ids)
        rounds.append(
            CountryQuizRound(
                country_id=correct_id,
                option_country_ids=tuple(option_ids),
            )
        )
    return BuildCountryQuizOutput(rounds=tuple(rounds))


def build_training_order(country_ids: Sequence[int]) -> list[int]:
    """Случайный порядок стран для режима Тренировка."""
    pool = list(dict.fromkeys(country_ids))
    random.shuffle(pool)
    return pool


def clip_to_questions_per_game(country_ids: Sequence[int], questions_per_game: int) -> list[int]:
    """Оставляет не больше questions_per_game стран, сохраняя уже выбранный порядок."""
    if questions_per_game <= 0:
        return []
    return list(country_ids)[:questions_per_game]


def format_int_ru(value: int) -> str:
    """Число с пробелом как разделителем тысяч."""
    return f"{value:,}".replace(",", " ")


def iso2_to_flag_emoji(iso2: str) -> str:
    """Флаг по ISO 3166-1 alpha-2: пара региональных индикаторов."""
    code = (iso2 or "").strip().upper()
    if len(code) != 2 or not code.isascii() or not code.isalpha():
        raise ValueError(f"iso2 must be two letters, got {iso2!r}")
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in code)


def format_country_card(
    *,
    name_ru: str,
    capital_ru: str,
    area_km2: float | None,
    population: int | None,
    flag: str = "",
) -> str:
    """Текст карточки страны для режима Тренировка."""
    area_text = "—"
    if area_km2 is not None:
        area_text = f"{format_int_ru(int(round(area_km2)))} км²"

    population_text = "—"
    if population is not None:
        population_text = format_int_ru(int(population))

    capital = (capital_ru or "").strip() or "—"
    mark = (flag or "").strip() or "🌍"
    return (
        f"{mark} {name_ru}\n"
        f"Столица: {capital}\n"
        f"Площадь: {area_text}\n"
        f"Население: {population_text}"
    )


def is_scored_mode_type(mode_type: str) -> bool:
    """Режимы, которые учитываются в рейтинге."""
    return mode_type in {"quiz", "country_flags", "country_map"}

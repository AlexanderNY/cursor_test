"""Unit-тесты движка режимов по странам."""

from __future__ import annotations

from unittest.mock import patch

from services.game_engine import (
    BuildCountryQuizInput,
    build_country_quiz_rounds,
    build_training_order,
    format_country_card,
    format_int_ru,
    is_scored_mode_type,
)


def test_build_country_quiz_rounds_basic() -> None:
    ids = list(range(1, 21))

    def _shuffle(items: list) -> None:
        items.sort(reverse=True)

    with patch("services.game_engine.random.shuffle", side_effect=_shuffle):
        out = build_country_quiz_rounds(
            BuildCountryQuizInput(
                country_ids=ids,
                questions_per_game=10,
                options_per_question=6,
            )
        )
    assert len(out.rounds) == 10
    seen_correct: set[int] = set()
    for round_row in out.rounds:
        assert round_row.country_id not in seen_correct
        seen_correct.add(round_row.country_id)
        opts = list(round_row.option_country_ids)
        assert len(opts) == 6
        assert len(set(opts)) == 6
        assert round_row.country_id in opts


def test_build_country_quiz_rounds_too_few_countries() -> None:
    out = build_country_quiz_rounds(
        BuildCountryQuizInput(
            country_ids=[1, 2, 3],
            questions_per_game=10,
            options_per_question=6,
        )
    )
    assert out.rounds == ()


def test_build_training_order_unique() -> None:
    ids = [1, 2, 2, 3, 4]
    with patch("services.game_engine.random.shuffle", lambda x: x.reverse()):
        ordered = build_training_order(ids)
    assert ordered == [4, 3, 2, 1]


def test_format_int_ru() -> None:
    assert format_int_ru(1_234_567) == "1 234 567"
    assert format_int_ru(42) == "42"


def test_format_country_card() -> None:
    text = format_country_card(
        name_ru="Россия",
        capital_ru="Москва",
        area_km2=17_098_242,
        population=144_478_050,
    )
    assert "Россия" in text
    assert "Москва" in text
    assert "км²" in text
    assert "144 478 050" in text


def test_format_country_card_missing_facts() -> None:
    text = format_country_card(
        name_ru="Тест",
        capital_ru="",
        area_km2=None,
        population=None,
    )
    assert "Столица: —" in text
    assert "Площадь: —" in text
    assert "Население: —" in text


def test_is_scored_mode_type() -> None:
    assert is_scored_mode_type("quiz") is True
    assert is_scored_mode_type("country_flags") is True
    assert is_scored_mode_type("country_map") is True
    assert is_scored_mode_type("country_training") is False
    assert is_scored_mode_type("menu") is False

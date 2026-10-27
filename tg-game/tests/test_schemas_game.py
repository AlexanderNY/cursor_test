"""Валидация Pydantic-схем игры."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas_game import (
    GameCountryCreate,
    GameCountryUpdate,
    GameModeCreate,
    GameOptionInput,
    GameQuestionCreate,
)


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


def test_country_create_normalizes_iso2() -> None:
    body = GameCountryCreate(iso2=" fr ", name_ru=" Франция ")
    assert body.iso2 == "FR"
    assert body.name_ru == "Франция"


def test_country_create_rejects_bad_iso2() -> None:
    with pytest.raises(ValidationError):
        GameCountryCreate(iso2="FRA", name_ru="Франция")


def test_country_update_strips_name() -> None:
    body = GameCountryUpdate(name_ru="  Франция  ", capital_ru=" Париж ")
    assert body.name_ru == "Франция"
    assert body.capital_ru == "Париж"


def test_country_update_blank_name_rejected() -> None:
    with pytest.raises(ValidationError):
        GameCountryUpdate(name_ru="   ")


def test_country_update_blank_url_becomes_none() -> None:
    body = GameCountryUpdate(flag_image_url="  ")
    assert body.flag_image_url is None
    assert "flag_image_url" in body.model_fields_set


def test_country_update_negative_population_rejected() -> None:
    with pytest.raises(ValidationError):
        GameCountryUpdate(population=-1)


def test_game_mode_create_country_types() -> None:
    for mode_type in ("country_training", "country_flags", "country_map"):
        body = GameModeCreate(
            bot_id=1,
            code=mode_type,
            title=mode_type,
            mode_type=mode_type,  # type: ignore[arg-type]
        )
        assert body.mode_type == mode_type

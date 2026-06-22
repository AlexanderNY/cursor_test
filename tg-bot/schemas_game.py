"""Pydantic-схемы для игры и админ-API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GameOptionInput(BaseModel):
    option_index: int = Field(ge=1, le=6)
    option_text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class GameModeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    questions_per_game: int = Field(ge=1, le=100)
    is_active: bool = True


class GameModeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    questions_per_game: Optional[int] = Field(default=None, ge=1, le=100)


class GameModeOut(BaseModel):
    id: int
    code: str
    title: str
    is_active: bool
    questions_per_game: int


class GameQuestionCreate(BaseModel):
    mode_id: int
    prompt_text: str = Field(min_length=1, max_length=4000)
    image_file_id: Optional[str] = None
    image_url: Optional[str] = None
    options: list[GameOptionInput]

    @field_validator("options")
    @classmethod
    def validate_six_options(cls, v: list[GameOptionInput]) -> list[GameOptionInput]:
        if len(v) != 6:
            raise ValueError("Must provide exactly 6 options")
        indices = sorted(o.option_index for o in v)
        if indices != [1, 2, 3, 4, 5, 6]:
            raise ValueError("option_index must be 1..6 with no duplicates")
        if sum(1 for o in v if o.is_correct) != 1:
            raise ValueError("Exactly one option must be marked is_correct=True")
        return v


class GameQuestionUpdate(BaseModel):
    prompt_text: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    image_file_id: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class GameQuestionOptionsReplace(BaseModel):
    options: list[GameOptionInput]

    @field_validator("options")
    @classmethod
    def validate_six_options(cls, v: list[GameOptionInput]) -> list[GameOptionInput]:
        if len(v) != 6:
            raise ValueError("Must provide exactly 6 options")
        indices = sorted(o.option_index for o in v)
        if indices != [1, 2, 3, 4, 5, 6]:
            raise ValueError("option_index must be 1..6 with no duplicates")
        if sum(1 for o in v if o.is_correct) != 1:
            raise ValueError("Exactly one option must be marked is_correct=True")
        return v


class GameQuestionOut(BaseModel):
    id: int
    mode_id: int
    prompt_text: str
    image_file_id: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool


class LeaderboardEntryOut(BaseModel):
    telegram_user_id: int
    username: Optional[str] = None
    score: int
    duration_sec: Optional[int] = None
    finished_at: Optional[str] = None

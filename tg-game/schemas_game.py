"""Pydantic-схемы для игры и админ-API."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class GameOptionInput(BaseModel):
    option_index: int = Field(ge=1, le=6)
    option_text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class GameModeCreate(BaseModel):
    bot_id: int = Field(ge=1)
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    questions_per_game: int = Field(default=10, ge=1, le=300)
    is_active: bool = True
    mode_type: Literal["quiz", "menu"] = "quiz"


class GameModeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    questions_per_game: Optional[int] = Field(default=None, ge=1, le=300)
    mode_type: Optional[Literal["quiz", "menu"]] = None


class GameModeOut(BaseModel):
    id: int
    bot_id: int
    code: str
    title: str
    is_active: bool
    questions_per_game: int
    mode_type: Literal["quiz", "menu"] = "quiz"


class GameBotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    token: str = Field(min_length=10, max_length=256)
    is_active: bool = True


class GameBotUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    token: Optional[str] = Field(default=None, min_length=10, max_length=256)
    is_active: Optional[bool] = None


class GameBotOut(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    token: str
    token_masked: str
    is_active: bool
    is_polling: bool = False
    created_at: Optional[str] = None


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


class GameOptionOut(BaseModel):
    id: int
    option_index: int
    option_text: str
    is_correct: bool


class GameQuestionDetailOut(GameQuestionOut):
    options: list[GameOptionOut]


class LeaderboardEntryOut(BaseModel):
    telegram_user_id: int
    username: Optional[str] = None
    score: int
    correct_count: int
    total_questions: int
    duration_sec: Optional[int] = None
    finished_at: Optional[str] = None


class GameSessionStatsOut(BaseModel):
    session_id: int
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    mode_id: int
    mode_title: str
    correct_count: int
    total_questions: int
    score: int
    duration_sec: Optional[int] = None
    finished_at: Optional[str] = None


class GameMediaUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


class GameMediaOut(BaseModel):
    id: int
    filename: str
    s3_key: str
    original_filename: Optional[str] = None
    title: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int
    created_at: str
    public_url: str


def _normalize_menu_price(value: float | int | str | Decimal) -> float:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid price format") from exc
    if decimal_value < 0:
        raise ValueError("Price must be non-negative")
    quantized = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if decimal_value != quantized:
        raise ValueError("Price must have at most 2 decimal places")
    return float(quantized)


class GameMenuNodeCreate(BaseModel):
    mode_id: int
    parent_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    body_text: Optional[str] = Field(default=None, max_length=4000)
    image_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    price: float = Field(default=0, ge=0)

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: object) -> float:
        if v is None or v == "":
            return 0.0
        return _normalize_menu_price(v)  # type: ignore[arg-type]


class GameMenuNodeUpdate(BaseModel):
    parent_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    body_text: Optional[str] = Field(default=None, max_length=4000)
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    price: Optional[float] = Field(default=None, ge=0)

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: object) -> Optional[float]:
        if v is None or v == "":
            return None
        return _normalize_menu_price(v)  # type: ignore[arg-type]


class GameMenuNodeOut(BaseModel):
    id: int
    mode_id: int
    parent_id: Optional[int] = None
    title: str
    body_text: Optional[str] = None
    image_url: Optional[str] = None
    image_file_id: Optional[str] = None
    sort_order: int
    is_active: bool
    price: float = 0


class GameMenuOrderItemOut(BaseModel):
    id: int
    node_id: Optional[int] = None
    title: str
    quantity: int
    unit_price: float = 0
    line_total: float = 0


class GameMenuOrderOut(BaseModel):
    id: int
    order_number: str
    bot_id: int
    mode_id: int
    mode_title: str
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    total_amount: float = 0
    total_quantity: int = 0
    items: list[GameMenuOrderItemOut] = []

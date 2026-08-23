from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


CredType = Literal["password", "jwt"]
ScenarioFormat = Literal["yaml", "json", "playwright_py"]
RunStatus = Literal["queued", "running", "passed", "failed"]


class CredentialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cred_type: CredType
    username: str | None = None
    password: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    meta: str | None = None


class CredentialOut(BaseModel):
    id: int
    name: str
    cred_type: CredType
    meta: str | None = None
    created_at: datetime


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    format: ScenarioFormat
    source: str = Field(min_length=1)
    credentials_id: int | None = None


class ScenarioOut(BaseModel):
    id: int
    name: str
    format: ScenarioFormat
    source: str
    credentials_id: int | None = None
    created_at: datetime


class RunCreate(BaseModel):
    scenario_id: int
    credentials_id: int | None = None


class RunEventOut(BaseModel):
    id: int
    ts: datetime
    level: str
    message: str


class ArtifactOut(BaseModel):
    id: int
    kind: str
    path: str
    step_name: str | None = None
    created_at: datetime
    url: str | None = None


class RunOut(BaseModel):
    id: int
    scenario_id: int
    credentials_id: int | None = None
    status: RunStatus
    error_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    events: list[RunEventOut] = Field(default_factory=list)
    artifacts: list[ArtifactOut] = Field(default_factory=list)


class HealthOut(BaseModel):
    status: str
    target_ui_url: str
    target_api_url: str
    details: dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


CredType = Literal["password", "jwt"]
ScenarioFormat = Literal["yaml", "json", "playwright_py"]
RunStatus = Literal["queued", "running", "passed", "failed"]
ResultStatus = Literal["passed", "failed", "skipped"]
NodeType = Literal["section", "subsection", "action"]


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


class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2000)
    meta: dict[str, Any] | str | None = None


class SiteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None, min_length=1, max_length=2000)
    meta: dict[str, Any] | str | None = None


class SiteOut(BaseModel):
    id: int
    name: str
    base_url: str
    meta: str | None = None
    created_at: datetime


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    format: ScenarioFormat
    source: str = Field(min_length=1)
    credentials_id: int | None = None
    site_id: int | None = None


class ScenarioOut(BaseModel):
    id: int
    name: str
    format: ScenarioFormat
    source: str
    credentials_id: int | None = None
    site_id: int | None = None
    schema_version: int = 1
    created_at: datetime


class RunCreate(BaseModel):
    scenario_id: int
    credentials_id: int | None = None
    site_id: int | None = None
    base_url: str | None = None


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
    result_id: int | None = None
    created_at: datetime
    url: str | None = None


class RunResultOut(BaseModel):
    id: int
    parent_id: int | None = None
    node_type: NodeType
    key: str | None = None
    title: str | None = None
    status: ResultStatus
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    sort_order: int = 0
    children: list[RunResultOut] = Field(default_factory=list)


class RunSummary(BaseModel):
    sections_passed: int = 0
    sections_failed: int = 0
    subsections_passed: int = 0
    subsections_failed: int = 0
    actions_passed: int = 0
    actions_failed: int = 0
    actions_skipped: int = 0


class RunOut(BaseModel):
    id: int
    scenario_id: int
    credentials_id: int | None = None
    site_id: int | None = None
    base_url_snapshot: str | None = None
    summary: RunSummary | None = None
    status: RunStatus
    error_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    events: list[RunEventOut] = Field(default_factory=list)
    artifacts: list[ArtifactOut] = Field(default_factory=list)
    results: list[RunResultOut] = Field(default_factory=list)


class HealthOut(BaseModel):
    status: str
    target_ui_url: str
    target_api_url: str
    details: dict[str, Any] = Field(default_factory=dict)


DiscoveryStatus = Literal["queued", "running", "completed", "failed"]
DiscoveryItemKind = Literal["link", "button", "input", "nav"]


class DiscoveryCreate(BaseModel):
    base_url: str | None = None
    site_id: int | None = None
    credentials_id: int | None = None
    max_pages: int = Field(default=40, ge=1, le=200)
    max_depth: int = Field(default=3, ge=0, le=10)
    same_origin_only: bool = True
    do_login: bool = False


class DiscoveryItemOut(BaseModel):
    id: int
    discovery_id: int
    kind: DiscoveryItemKind
    page_url: str | None = None
    page_path: str | None = None
    href: str | None = None
    path: str | None = None
    label: str | None = None
    selector: str | None = None
    text: str | None = None
    interactive: bool = True
    selected: bool = False
    meta: str | None = None
    sort_order: int = 0
    created_at: datetime


class DiscoveryOut(BaseModel):
    id: int
    site_id: int | None = None
    credentials_id: int | None = None
    base_url: str
    status: DiscoveryStatus
    max_pages: int
    max_depth: int
    same_origin_only: bool
    do_login: bool
    error_summary: str | None = None
    summary: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    items: list[DiscoveryItemOut] = Field(default_factory=list)


class DiscoverySelectBody(BaseModel):
    item_ids: list[int] = Field(default_factory=list)
    selected: bool = True


class DiscoveryToScenarioBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    item_ids: list[int] | None = None
    include_login: bool = True
    credentials_id: int | None = None


RunResultOut.model_rebuild()

from __future__ import annotations

import ast
import json
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

FORBIDDEN_MODULES = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "pathlib",
        "shutil",
        "ctypes",
        "importlib",
        "builtins",
        "pickle",
        "http",
        "urllib",
        "requests",
        "aiohttp",
        "httpx",
    }
)

KNOWN_ACTIONS = frozenset(
    {
        "goto",
        "fill",
        "type",
        "click",
        "wait",
        "wait_url",
        "assert_text",
        "assert_url",
        "screenshot",
        "login_form",
    }
)


class ActionStep(BaseModel):
    action: str
    path: str | None = None
    url: str | None = None
    selector: str | None = None
    value: str | None = None
    value_from: str | None = None
    ms: int | None = None
    timeout_ms: int | None = None
    contains: str | None = None
    name: str | None = None

    model_config = {"extra": "allow"}

    @field_validator("action")
    @classmethod
    def action_known(cls, value: str) -> str:
        if value not in KNOWN_ACTIONS:
            raise ValueError(f"unknown action: {value}")
        return value


class SubsectionNode(BaseModel):
    id: str
    title: str | None = None
    on_enter: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)


class SectionNode(BaseModel):
    id: str
    title: str | None = None
    on_enter: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    subsections: list[SubsectionNode] = Field(default_factory=list)


class ScenarioDocument(BaseModel):
    schema_version: int = 1
    name: str | None = None
    site: str | None = None
    base_url: str | None = None
    defaults: dict[str, Any] = Field(default_factory=dict)
    sections: list[SectionNode] = Field(default_factory=list)


def _validate_actions(actions: list[Any], path: str) -> list[dict[str, Any]]:
    if not isinstance(actions, list):
        raise ValueError(f"{path} must be a list")
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(actions):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}[{index}] must be a mapping")
        if not raw.get("action"):
            raise ValueError(f"{path}[{index}]: missing action")
        ActionStep.model_validate(raw)
        out.append(raw)
    return out


def _parse_sections(raw_sections: list[Any]) -> list[SectionNode]:
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError("scenario must include a non-empty sections list")
    sections: list[SectionNode] = []
    for index, raw in enumerate(raw_sections):
        if not isinstance(raw, dict):
            raise ValueError(f"sections[{index}] must be a mapping")
        section_id = str(raw.get("id") or f"section_{index + 1}")
        subsections_raw = raw.get("subsections") or []
        if not isinstance(subsections_raw, list):
            raise ValueError(f"sections[{index}].subsections must be a list")
        subsections: list[SubsectionNode] = []
        for sub_index, sub in enumerate(subsections_raw):
            if not isinstance(sub, dict):
                raise ValueError(f"sections[{index}].subsections[{sub_index}] must be a mapping")
            sub_id = str(sub.get("id") or f"sub_{sub_index + 1}")
            subsections.append(
                SubsectionNode(
                    id=sub_id,
                    title=sub.get("title"),
                    on_enter=_validate_actions(
                        sub.get("on_enter") or [],
                        f"sections[{index}].subsections[{sub_index}].on_enter",
                    ),
                    actions=_validate_actions(
                        sub.get("actions") or [],
                        f"sections[{index}].subsections[{sub_index}].actions",
                    ),
                )
            )
        actions = _validate_actions(raw.get("actions") or [], f"sections[{index}].actions")
        on_enter = _validate_actions(raw.get("on_enter") or [], f"sections[{index}].on_enter")
        if not actions and not subsections and not on_enter:
            raise ValueError(f"sections[{index}] must have on_enter, actions, or subsections")
        sections.append(
            SectionNode(
                id=section_id,
                title=raw.get("title"),
                on_enter=on_enter,
                actions=actions,
                subsections=subsections,
            )
        )
    return sections


def detect_schema_version(data: dict[str, Any]) -> int:
    if "schema_version" in data:
        try:
            return int(data["schema_version"])
        except (TypeError, ValueError) as exc:
            raise ValueError("schema_version must be an integer") from exc
    if "sections" in data:
        return 2
    return 1


def normalize_scenario(data: dict[str, Any]) -> ScenarioDocument:
    version = detect_schema_version(data)
    defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
    base_url = data.get("base_url")
    site = data.get("site")
    name = data.get("name")

    if version >= 2 or "sections" in data:
        sections = _parse_sections(data.get("sections") or [])
        return ScenarioDocument(
            schema_version=max(version, 2),
            name=name,
            site=site,
            base_url=base_url,
            defaults=defaults,
            sections=sections,
        )

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("scenario must include a non-empty steps list")
    validated = _validate_actions(steps, "steps")
    return ScenarioDocument(
        schema_version=1,
        name=name,
        site=site,
        base_url=base_url,
        defaults=defaults,
        sections=[
            SectionNode(
                id="main",
                title=str(name or "main"),
                actions=validated,
            )
        ],
    )


def parse_scenario_document(source: str, fmt: str) -> ScenarioDocument:
    if fmt == "yaml":
        data = yaml.safe_load(source)
    elif fmt == "json":
        data = json.loads(source)
    else:
        raise ValueError(f"cannot parse structured scenario for format={fmt}")
    if not isinstance(data, dict):
        raise ValueError("scenario root must be a mapping")
    return normalize_scenario(data)


def validate_playwright_script(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"invalid Python script: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_MODULES:
                    raise ValueError(f"forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_MODULES:
                    raise ValueError(f"forbidden import: {node.module}")
        elif isinstance(node, (ast.Call,)):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "eval",
                "exec",
                "__import__",
                "open",
            }:
                raise ValueError(f"forbidden call: {node.func.id}")

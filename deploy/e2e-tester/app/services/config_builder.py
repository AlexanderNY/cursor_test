from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field


class LoginConfig(BaseModel):
    enabled: bool = True
    path: str = "/sign-in"
    username_selector: str = 'input[placeholder="Enter your username"]'
    password_selector: str = 'input[type="password"]'
    submit_selector: str = 'button[type="submit"]'
    success_url_contains: str | None = "/profile"
    success_text: str | None = "Profile"
    success_text_selector: str = "body"
    screenshot_name: str = "login"


class ButtonConfig(BaseModel):
    """Кнопка/элемент для клика внутри раздела."""

    label: str | None = None
    selector: str | None = None
    text: str | None = None
    wait_ms: int | None = 1000
    assert_text: str | None = None
    assert_selector: str = "body"


class PageSectionConfig(BaseModel):
    """Раздел сайта: переход по ссылке + проверки + кнопки."""

    id: str | None = None
    title: str
    path: str
    assert_text: str | None = None
    assert_selector: str = "body"
    assert_url_contains: str | None = None
    screenshot: bool = True
    buttons: list[ButtonConfig] = Field(default_factory=list)


class ScenarioConfigCreate(BaseModel):
    """Пользовательская конфигурация → JSON scenario v2."""

    name: str = Field(min_length=1, max_length=200)
    site_name: str | None = None
    base_url: str = Field(min_length=1, max_length=2000)
    site_id: int | None = None
    credentials_id: int | None = None
    create_credential: bool = False
    credential_name: str | None = None
    username: str | None = None
    password: str | None = None
    timeout_ms: int = 30000
    login: LoginConfig = Field(default_factory=LoginConfig)
    pages: list[PageSectionConfig] = Field(default_factory=list)


def _slug(value: str, fallback: str = "item") -> str:
    raw = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return (raw or fallback)[:64]


def _button_selector(btn: ButtonConfig) -> str:
    if btn.selector:
        return btn.selector
    if btn.text:
        safe = btn.text.replace('"', '\\"')
        return f'button:has-text("{safe}")'
    raise ValueError("button requires selector or text")


def build_scenario_document(cfg: ScenarioConfigCreate) -> dict[str, Any]:
    if not cfg.pages and not (cfg.login and cfg.login.enabled):
        raise ValueError("config must include login and/or at least one page section")

    site_name = cfg.site_name or _slug(cfg.name, "site")
    defaults: dict[str, Any] = {
        "timeout_ms": cfg.timeout_ms,
        "login": {
            "path": cfg.login.path,
            "username_selector": cfg.login.username_selector,
            "password_selector": cfg.login.password_selector,
            "submit_selector": cfg.login.submit_selector,
        },
    }

    sections: list[dict[str, Any]] = []

    if cfg.login.enabled:
        actions: list[dict[str, Any]] = [{"action": "login_form"}]
        if cfg.login.success_url_contains:
            actions.append(
                {
                    "action": "wait_url",
                    "contains": cfg.login.success_url_contains,
                    "timeout_ms": cfg.timeout_ms,
                }
            )
        if cfg.login.success_text:
            actions.append(
                {
                    "action": "assert_text",
                    "selector": cfg.login.success_text_selector or "body",
                    "contains": cfg.login.success_text,
                }
            )
        actions.append({"action": "screenshot", "name": cfg.login.screenshot_name or "login"})
        sections.append({"id": "auth", "title": "Login", "actions": actions})

    for index, page in enumerate(cfg.pages, start=1):
        page_id = page.id or _slug(page.title or page.path, f"page_{index}")
        assert_url = page.assert_url_contains or page.path
        on_enter = [{"action": "goto", "path": page.path}]
        actions = [
            {
                "action": "wait_url",
                "contains": assert_url,
                "timeout_ms": cfg.timeout_ms,
            }
        ]
        if page.assert_text:
            actions.append(
                {
                    "action": "assert_text",
                    "selector": page.assert_selector or "body",
                    "contains": page.assert_text,
                }
            )
        for b_index, btn in enumerate(page.buttons, start=1):
            actions.append({"action": "click", "selector": _button_selector(btn)})
            if btn.wait_ms:
                actions.append({"action": "wait", "ms": int(btn.wait_ms)})
            if btn.assert_text:
                actions.append(
                    {
                        "action": "assert_text",
                        "selector": btn.assert_selector or "body",
                        "contains": btn.assert_text,
                    }
                )
            label = btn.label or btn.text or f"btn_{b_index}"
            actions.append(
                {
                    "action": "screenshot",
                    "name": f"{page_id}_{_slug(label, f'btn_{b_index}')}",
                }
            )
        if page.screenshot and not page.buttons:
            actions.append({"action": "screenshot", "name": page_id})
        elif page.screenshot and page.buttons:
            # final page shot after buttons
            actions.append({"action": "screenshot", "name": f"{page_id}_done"})

        sections.append(
            {
                "id": page_id,
                "title": page.title,
                "on_enter": on_enter,
                "actions": actions,
            }
        )

    return {
        "schema_version": 2,
        "name": cfg.name,
        "site": site_name,
        "base_url": cfg.base_url.rstrip("/"),
        "defaults": defaults,
        "sections": sections,
    }


def build_scenario_source(cfg: ScenarioConfigCreate) -> str:
    doc = build_scenario_document(cfg)
    return json.dumps(doc, ensure_ascii=False, indent=2)

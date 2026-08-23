from __future__ import annotations

import asyncio
import logging
import traceback
from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import Browser, Page, async_playwright

from app.config import get_settings
from app.db import execute, execute_returning
from app.services.crypto import decrypt_payload
from app.services.scenario_loader import parse_scenario_document, validate_playwright_script

logger = logging.getLogger(__name__)

LogFn = Callable[[str, str], Awaitable[None]]


async def _append_event(run_id: int, level: str, message: str) -> None:
    await execute(
        "INSERT INTO run_events (run_id, level, message) VALUES (%s, %s, %s)",
        (run_id, level, message[:4000]),
    )


async def _add_artifact(
    run_id: int,
    kind: str,
    path: str,
    step_name: str | None,
) -> None:
    await execute(
        "INSERT INTO artifacts (run_id, kind, path, step_name) VALUES (%s, %s, %s, %s)",
        (run_id, kind, path, step_name),
    )


async def _screenshot(page: Page, run_id: int, step_name: str) -> str | None:
    settings = get_settings()
    run_dir = settings.artifacts_path / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in step_name)[:80]
    file_path = run_dir / f"{safe}.png"
    try:
        await page.screenshot(path=str(file_path), full_page=True)
    except Exception as exc:
        logger.warning("screenshot failed: %s", exc)
        return None
    rel = f"{run_id}/{file_path.name}"
    await _add_artifact(run_id, "screenshot", rel, step_name)
    return rel


def _resolve_value(step: dict[str, Any], credentials: dict[str, Any] | None) -> str:
    if "value" in step and step["value"] is not None:
        return str(step["value"])
    value_from = step.get("value_from")
    if not value_from:
        raise ValueError("fill step requires value or value_from")
    if credentials is None:
        raise ValueError("credentials required for value_from")
    mapping = {
        "credentials.username": credentials.get("username"),
        "credentials.password": credentials.get("password"),
        "credentials.access_token": credentials.get("access_token"),
        "credentials.refresh_token": credentials.get("refresh_token"),
    }
    if value_from not in mapping:
        raise ValueError(f"unknown value_from: {value_from}")
    val = mapping[value_from]
    if val is None:
        raise ValueError(f"credentials missing field for {value_from}")
    return str(val)


async def _inject_jwt(page: Page, credentials: dict[str, Any], base_url: str) -> None:
    access = credentials.get("access_token") or ""
    refresh = credentials.get("refresh_token") or ""
    await page.add_init_script(
        """([access, refresh]) => {
            try {
                localStorage.setItem('access_token', access);
                if (refresh) localStorage.setItem('refresh_token', refresh);
            } catch (e) {}
        }""",
        [access, refresh],
    )
    # Ensure origin exists so localStorage is available
    await page.goto(base_url.rstrip("/") + "/", wait_until="domcontentloaded")


async def _run_login_form(page: Page, credentials: dict[str, Any], base_url: str, log: LogFn) -> None:
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise ValueError("login_form requires password credentials with username/password")
    url = base_url.rstrip("/") + "/sign-in"
    await log("info", f"login_form → {url}")
    await page.goto(url, wait_until="domcontentloaded")
    user_sel = 'input[placeholder="Enter your username"]'
    pass_sel = 'input[type="password"]'
    await page.fill(user_sel, username)
    await page.fill(pass_sel, password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")


async def _run_step(
    page: Page,
    step: dict[str, Any],
    index: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    log: LogFn,
) -> None:
    action = step.get("action")
    if not action:
        raise ValueError(f"step {index}: missing action")
    await log("info", f"step {index}: {action}")

    if action == "goto":
        path = step.get("path") or step.get("url") or "/"
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            url = base_url.rstrip("/") + "/" + str(path).lstrip("/")
        await page.goto(url, wait_until="domcontentloaded")
        return

    if action == "fill":
        selector = step["selector"]
        value = _resolve_value(step, credentials)
        await page.fill(selector, value)
        return

    if action == "click":
        await page.click(step["selector"])
        return

    if action == "wait":
        ms = int(step.get("ms") or step.get("timeout_ms") or 1000)
        await page.wait_for_timeout(ms)
        return

    if action == "wait_url":
        contains = step.get("contains") or ""
        timeout = int(step.get("timeout_ms") or 15000)
        await page.wait_for_function(
            """(needle) => window.location.href.includes(needle)""",
            contains,
            timeout=timeout,
        )
        return

    if action == "assert_text":
        selector = step.get("selector") or "body"
        contains = step.get("contains") or ""
        text = await page.locator(selector).inner_text()
        if contains not in text:
            raise AssertionError(f"assert_text: '{contains}' not found in {selector}")
        return

    if action == "assert_url":
        contains = step.get("contains") or ""
        if contains not in page.url:
            raise AssertionError(f"assert_url: '{contains}' not in {page.url}")
        return

    if action == "screenshot":
        # caller handles named screenshots via log path; here just a marker
        await log("info", f"screenshot marker: {step.get('name') or f'step_{index}'}")
        return

    if action == "login_form":
        if credentials is None:
            raise ValueError("login_form requires credentials")
        await _run_login_form(page, credentials, base_url, log)
        return

    raise ValueError(f"unknown action: {action}")


async def _run_yaml_steps(
    page: Page,
    doc: dict[str, Any],
    base_url: str,
    credentials: dict[str, Any] | None,
    run_id: int,
    log: LogFn,
) -> None:
    steps = doc["steps"]
    for index, raw in enumerate(steps, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"step {index} must be a mapping")
        try:
            await _run_step(page, raw, index, base_url, credentials, log)
            if raw.get("action") == "screenshot":
                name = str(raw.get("name") or f"step_{index}")
                await _screenshot(page, run_id, name)
        except Exception:
            await _screenshot(page, run_id, f"error_step_{index}")
            raise


async def _run_playwright_py(
    page: Page,
    source: str,
    base_url: str,
    credentials: dict[str, Any] | None,
    log: LogFn,
) -> None:
    validate_playwright_script(source)
    safe_builtins = {
        "True": True,
        "False": False,
        "None": None,
        "str": str,
        "int": int,
        "float": float,
        "len": len,
        "print": lambda *a, **k: None,
        "range": range,
        "dict": dict,
        "list": list,
        "min": min,
        "max": max,
        "Exception": Exception,
        "AssertionError": AssertionError,
        "ValueError": ValueError,
    }

    async def script_log(msg: str) -> None:
        await log("info", str(msg))

    globals_dict: dict[str, Any] = {
        "__builtins__": safe_builtins,
        "page": page,
        "base_url": base_url,
        "credentials": credentials or {},
        "log": script_log,
        "asyncio": asyncio,
    }
    # Compile and exec in a restricted env; script may define async def run(page, ...)
    exec(compile(source, "<scenario>", "exec"), globals_dict, globals_dict)
    run_fn = globals_dict.get("run")
    if run_fn is None:
        raise ValueError("playwright_py script must define async def run(page, base_url, credentials, log)")
    result = run_fn(page, base_url, credentials or {}, script_log)
    if asyncio.iscoroutine(result):
        await result


async def execute_run(
    run_id: int,
    scenario: dict[str, Any],
    credentials_row: dict[str, Any] | None,
) -> None:
    settings = get_settings()
    base_url = settings.TARGET_UI_URL.rstrip("/")
    settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    credentials: dict[str, Any] | None = None
    if credentials_row is not None:
        credentials = decrypt_payload(credentials_row["payload_encrypted"])

    async def log(level: str, message: str) -> None:
        # Never log secrets
        await _append_event(run_id, level, message)

    await execute(
        "UPDATE runs SET status = 'running', started_at = NOW(), error_summary = NULL WHERE id = %s",
        (run_id,),
    )
    await log("info", f"run started; target={base_url}")

    browser: Browser | None = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()

            if credentials_row and credentials_row["cred_type"] == "jwt" and credentials:
                await log("info", "injecting JWT into localStorage")
                await _inject_jwt(page, credentials, base_url)

            try:
                fmt = scenario["format"]
                if fmt in ("yaml", "json"):
                    doc = parse_scenario_document(scenario["source"], fmt)
                    await _run_yaml_steps(page, doc, base_url, credentials, run_id, log)
                elif fmt == "playwright_py":
                    await _run_playwright_py(
                        page, scenario["source"], base_url, credentials, log
                    )
                else:
                    raise ValueError(f"unsupported format: {fmt}")
            except Exception:
                await _screenshot(page, run_id, "error_final")
                raise
            finally:
                await context.close()
                await browser.close()
                browser = None

        await execute(
            "UPDATE runs SET status = 'passed', finished_at = NOW() WHERE id = %s",
            (run_id,),
        )
        await log("info", "run passed")
    except Exception as exc:
        summary = f"{type(exc).__name__}: {exc}"
        logger.exception("run %s failed", run_id)
        await execute(
            "UPDATE runs SET status = 'failed', finished_at = NOW(), error_summary = %s WHERE id = %s",
            (summary[:2000], run_id),
        )
        await log("error", summary)
        await log("error", traceback.format_exc()[-2000:])
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass

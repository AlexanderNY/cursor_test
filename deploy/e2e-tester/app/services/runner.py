from __future__ import annotations

import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from playwright.async_api import Browser, Page, async_playwright

from app.config import get_settings
from app.db import execute, execute_returning, fetch_one
from app.schemas.models import RunSummary
from app.services.crypto import decrypt_payload
from app.services.scenario_loader import (
    ScenarioDocument,
    SectionNode,
    SubsectionNode,
    parse_scenario_document,
    validate_playwright_script,
)

logger = logging.getLogger(__name__)

LogFn = Callable[[str, str], Awaitable[None]]

DEFAULT_LOGIN = {
    "path": "/sign-in",
    "username_selector": 'input[placeholder="Enter your username"]',
    "password_selector": 'input[type="password"]',
    "submit_selector": 'button[type="submit"]',
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _merge_login_config(
    site_meta: dict[str, Any] | None,
    defaults: dict[str, Any] | None,
) -> dict[str, str]:
    cfg = dict(DEFAULT_LOGIN)
    if site_meta and isinstance(site_meta.get("login"), dict):
        cfg.update({k: str(v) for k, v in site_meta["login"].items() if v is not None})
    if defaults and isinstance(defaults.get("login"), dict):
        cfg.update({k: str(v) for k, v in defaults["login"].items() if v is not None})
    return cfg


def _parse_meta(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


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
    result_id: int | None = None,
) -> None:
    await execute(
        """
        INSERT INTO artifacts (run_id, result_id, kind, path, step_name)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (run_id, result_id, kind, path, step_name),
    )


async def _screenshot(
    page: Page,
    run_id: int,
    step_name: str,
    result_id: int | None = None,
) -> str | None:
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
    await _add_artifact(run_id, "screenshot", rel, step_name, result_id=result_id)
    return rel


async def _insert_result(
    run_id: int,
    parent_id: int | None,
    node_type: str,
    key: str | None,
    title: str | None,
    sort_order: int,
) -> int:
    row = await execute_returning(
        """
        INSERT INTO run_results (
            run_id, parent_id, node_type, key, title, status, started_at, sort_order
        )
        VALUES (%s, %s, %s, %s, %s, 'passed', NOW(), %s)
        RETURNING id
        """,
        (run_id, parent_id, node_type, key, title, sort_order),
    )
    return int(row["id"])


async def _finish_result(
    result_id: int,
    status: str,
    error: str | None,
    started: datetime,
) -> None:
    finished = _utcnow()
    duration = int((finished - started).total_seconds() * 1000)
    await execute(
        """
        UPDATE run_results
        SET status = %s, error = %s, finished_at = NOW(), duration_ms = %s
        WHERE id = %s
        """,
        (status, (error or "")[:2000] or None, duration, result_id),
    )


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
    await page.goto(base_url.rstrip("/") + "/", wait_until="domcontentloaded")


async def _run_login_form(
    page: Page,
    credentials: dict[str, Any],
    base_url: str,
    login_cfg: dict[str, str],
    log: LogFn,
) -> None:
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise ValueError("login_form requires password credentials with username/password")
    path = login_cfg.get("path") or "/sign-in"
    url = base_url.rstrip("/") + "/" + str(path).lstrip("/")
    await log("info", f"login_form → {url}")
    await page.goto(url, wait_until="domcontentloaded")
    await page.fill(login_cfg["username_selector"], username)
    await page.fill(login_cfg["password_selector"], password)
    await page.click(login_cfg["submit_selector"])
    await page.wait_for_load_state("networkidle")


async def _run_step(
    page: Page,
    step: dict[str, Any],
    index: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    login_cfg: dict[str, str],
    log: LogFn,
) -> None:
    action = step.get("action")
    if not action:
        raise ValueError(f"step {index}: missing action")
    await log("info", f"step {index}: {action}")

    if action == "goto":
        path = step.get("path") or step.get("url") or "/"
        if str(path).startswith("http://") or str(path).startswith("https://"):
            url = str(path)
        else:
            url = base_url.rstrip("/") + "/" + str(path).lstrip("/")
        await page.goto(url, wait_until="domcontentloaded")
        return

    if action == "fill":
        selector = step["selector"]
        value = _resolve_value(step, credentials)
        await page.fill(selector, value)
        return

    if action == "type":
        # For TipTap / contenteditable where page.fill() does not work
        selector = step["selector"]
        value = _resolve_value(step, credentials)
        clear = bool(step.get("clear", True))
        loc = page.locator(selector).first
        await loc.click()
        if clear:
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
        await page.keyboard.type(value, delay=int(step.get("delay_ms") or 20))
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
        await log("info", f"screenshot marker: {step.get('name') or f'step_{index}'}")
        return

    if action == "login_form":
        if credentials is None:
            raise ValueError("login_form requires credentials")
        await _run_login_form(page, credentials, base_url, login_cfg, log)
        return

    raise ValueError(f"unknown action: {action}")


async def _run_action_list(
    page: Page,
    actions: list[dict[str, Any]],
    *,
    run_id: int,
    parent_id: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    login_cfg: dict[str, str],
    log: LogFn,
    label_prefix: str,
    fail_soft: bool,
) -> bool:
    """Run actions under parent. Returns True if all passed."""
    all_ok = True
    skip_rest = False
    for index, raw in enumerate(actions, start=1):
        title = str(raw.get("name") or raw.get("action") or f"action_{index}")
        key = f"{label_prefix}/{index}_{raw.get('action')}"
        started = _utcnow()
        result_id = await _insert_result(
            run_id, parent_id, "action", key, title, sort_order=index
        )
        if skip_rest:
            await _finish_result(result_id, "skipped", "skipped after previous failure", started)
            all_ok = False
            continue
        try:
            await _run_step(page, raw, index, base_url, credentials, login_cfg, log)
            if raw.get("action") == "screenshot":
                name = str(raw.get("name") or f"{label_prefix}_{index}")
                await _screenshot(page, run_id, name, result_id=result_id)
            await _finish_result(result_id, "passed", None, started)
        except Exception as exc:
            all_ok = False
            summary = f"{type(exc).__name__}: {exc}"
            await log("error", f"{key}: {summary}")
            await _screenshot(page, run_id, f"error_{label_prefix}_{index}", result_id=result_id)
            await _finish_result(result_id, "failed", summary, started)
            if fail_soft:
                skip_rest = True
            else:
                raise
    return all_ok


async def _run_subsection(
    page: Page,
    subsection: SubsectionNode,
    *,
    run_id: int,
    parent_id: int,
    sort_order: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    login_cfg: dict[str, str],
    log: LogFn,
) -> bool:
    started = _utcnow()
    title = subsection.title or subsection.id
    result_id = await _insert_result(
        run_id, parent_id, "subsection", subsection.id, title, sort_order
    )
    await log("info", f"subsection start: {subsection.id}")
    ok = True
    try:
        if subsection.on_enter:
            ok = await _run_action_list(
                page,
                subsection.on_enter,
                run_id=run_id,
                parent_id=result_id,
                base_url=base_url,
                credentials=credentials,
                login_cfg=login_cfg,
                log=log,
                label_prefix=f"{subsection.id}/enter",
                fail_soft=True,
            ) and ok
        if ok and subsection.actions:
            ok = await _run_action_list(
                page,
                subsection.actions,
                run_id=run_id,
                parent_id=result_id,
                base_url=base_url,
                credentials=credentials,
                login_cfg=login_cfg,
                log=log,
                label_prefix=subsection.id,
                fail_soft=True,
            ) and ok
        elif not ok and subsection.actions:
            for index, raw in enumerate(subsection.actions, start=1):
                title_a = str(raw.get("name") or raw.get("action") or f"action_{index}")
                started_a = _utcnow()
                aid = await _insert_result(
                    run_id,
                    result_id,
                    "action",
                    f"{subsection.id}/{index}_{raw.get('action')}",
                    title_a,
                    index + 1000,
                )
                await _finish_result(aid, "skipped", "skipped after on_enter failure", started_a)
        await _finish_result(result_id, "passed" if ok else "failed", None if ok else "subsection failed", started)
        return ok
    except Exception as exc:
        summary = f"{type(exc).__name__}: {exc}"
        await _finish_result(result_id, "failed", summary, started)
        return False


async def _run_section(
    page: Page,
    section: SectionNode,
    *,
    run_id: int,
    sort_order: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    login_cfg: dict[str, str],
    log: LogFn,
) -> bool:
    started = _utcnow()
    title = section.title or section.id
    result_id = await _insert_result(run_id, None, "section", section.id, title, sort_order)
    await log("info", f"section start: {section.id}")
    ok = True
    try:
        if section.on_enter:
            ok = await _run_action_list(
                page,
                section.on_enter,
                run_id=run_id,
                parent_id=result_id,
                base_url=base_url,
                credentials=credentials,
                login_cfg=login_cfg,
                log=log,
                label_prefix=f"{section.id}/enter",
                fail_soft=True,
            ) and ok

        if section.subsections:
            for sub_index, subsection in enumerate(section.subsections, start=1):
                sub_ok = await _run_subsection(
                    page,
                    subsection,
                    run_id=run_id,
                    parent_id=result_id,
                    sort_order=sub_index,
                    base_url=base_url,
                    credentials=credentials,
                    login_cfg=login_cfg,
                    log=log,
                )
                ok = sub_ok and ok
        elif section.actions:
            if ok:
                ok = await _run_action_list(
                    page,
                    section.actions,
                    run_id=run_id,
                    parent_id=result_id,
                    base_url=base_url,
                    credentials=credentials,
                    login_cfg=login_cfg,
                    log=log,
                    label_prefix=section.id,
                    fail_soft=True,
                ) and ok
            else:
                for index, raw in enumerate(section.actions, start=1):
                    title_a = str(raw.get("name") or raw.get("action") or f"action_{index}")
                    started_a = _utcnow()
                    aid = await _insert_result(
                        run_id,
                        result_id,
                        "action",
                        f"{section.id}/{index}_{raw.get('action')}",
                        title_a,
                        index + 1000,
                    )
                    await _finish_result(aid, "skipped", "skipped after on_enter failure", started_a)

        await _finish_result(result_id, "passed" if ok else "failed", None if ok else "section failed", started)
        return ok
    except Exception as exc:
        summary = f"{type(exc).__name__}: {exc}"
        await _finish_result(result_id, "failed", summary, started)
        return False


async def _run_document_tree(
    page: Page,
    doc: ScenarioDocument,
    *,
    run_id: int,
    base_url: str,
    credentials: dict[str, Any] | None,
    login_cfg: dict[str, str],
    log: LogFn,
) -> bool:
    all_ok = True
    for index, section in enumerate(doc.sections, start=1):
        section_ok = await _run_section(
            page,
            section,
            run_id=run_id,
            sort_order=index,
            base_url=base_url,
            credentials=credentials,
            login_cfg=login_cfg,
            log=log,
        )
        all_ok = section_ok and all_ok
    return all_ok


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
    exec(compile(source, "<scenario>", "exec"), globals_dict, globals_dict)
    run_fn = globals_dict.get("run")
    if run_fn is None:
        raise ValueError("playwright_py script must define async def run(page, base_url, credentials, log)")
    result = run_fn(page, base_url, credentials or {}, script_log)
    if asyncio.iscoroutine(result):
        await result


async def _build_summary(run_id: int) -> RunSummary:
    rows = await fetch_one(
        """
        SELECT
          COUNT(*) FILTER (WHERE node_type = 'section' AND status = 'passed') AS sections_passed,
          COUNT(*) FILTER (WHERE node_type = 'section' AND status = 'failed') AS sections_failed,
          COUNT(*) FILTER (WHERE node_type = 'subsection' AND status = 'passed') AS subsections_passed,
          COUNT(*) FILTER (WHERE node_type = 'subsection' AND status = 'failed') AS subsections_failed,
          COUNT(*) FILTER (WHERE node_type = 'action' AND status = 'passed') AS actions_passed,
          COUNT(*) FILTER (WHERE node_type = 'action' AND status = 'failed') AS actions_failed,
          COUNT(*) FILTER (WHERE node_type = 'action' AND status = 'skipped') AS actions_skipped
        FROM run_results
        WHERE run_id = %s
        """,
        (run_id,),
    )
    if rows is None:
        return RunSummary()
    return RunSummary(
        sections_passed=int(rows.get("sections_passed") or 0),
        sections_failed=int(rows.get("sections_failed") or 0),
        subsections_passed=int(rows.get("subsections_passed") or 0),
        subsections_failed=int(rows.get("subsections_failed") or 0),
        actions_passed=int(rows.get("actions_passed") or 0),
        actions_failed=int(rows.get("actions_failed") or 0),
        actions_skipped=int(rows.get("actions_skipped") or 0),
    )


async def execute_run(
    run_id: int,
    scenario: dict[str, Any],
    credentials_row: dict[str, Any] | None,
    *,
    base_url: str,
    site_meta: dict[str, Any] | None = None,
) -> None:
    settings = get_settings()
    base_url = base_url.rstrip("/")
    settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    credentials: dict[str, Any] | None = None
    if credentials_row is not None:
        credentials = decrypt_payload(credentials_row["payload_encrypted"])

    async def log(level: str, message: str) -> None:
        await _append_event(run_id, level, message)

    await execute(
        """
        UPDATE runs
        SET status = 'running', started_at = NOW(), error_summary = NULL,
            base_url_snapshot = %s, summary_json = NULL
        WHERE id = %s
        """,
        (base_url, run_id),
    )
    await execute("DELETE FROM run_results WHERE run_id = %s", (run_id,))
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

            passed = True
            try:
                fmt = scenario["format"]
                if fmt in ("yaml", "json"):
                    doc = parse_scenario_document(scenario["source"], fmt)
                    login_cfg = _merge_login_config(site_meta, doc.defaults)
                    passed = await _run_document_tree(
                        page,
                        doc,
                        run_id=run_id,
                        base_url=base_url,
                        credentials=credentials,
                        login_cfg=login_cfg,
                        log=log,
                    )
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

        summary = await _build_summary(run_id)
        summary_json = summary.model_dump_json()
        if passed:
            await execute(
                """
                UPDATE runs
                SET status = 'passed', finished_at = NOW(), summary_json = %s
                WHERE id = %s
                """,
                (summary_json, run_id),
            )
            await log("info", f"run passed; summary={summary_json}")
        else:
            err = "one or more sections/actions failed"
            await execute(
                """
                UPDATE runs
                SET status = 'failed', finished_at = NOW(), error_summary = %s, summary_json = %s
                WHERE id = %s
                """,
                (err, summary_json, run_id),
            )
            await log("error", err)
    except Exception as exc:
        summary = f"{type(exc).__name__}: {exc}"
        logger.exception("run %s failed", run_id)
        try:
            run_summary = await _build_summary(run_id)
            summary_json = run_summary.model_dump_json()
        except Exception:
            summary_json = None
        await execute(
            """
            UPDATE runs
            SET status = 'failed', finished_at = NOW(), error_summary = %s, summary_json = %s
            WHERE id = %s
            """,
            (summary[:2000], summary_json, run_id),
        )
        await log("error", summary)
        await log("error", traceback.format_exc()[-2000:])
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass

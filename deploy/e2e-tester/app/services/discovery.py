from __future__ import annotations

import json
import logging
import re
from collections import deque
from typing import Any
from urllib.parse import urldefrag, urlparse

from playwright.async_api import Page, async_playwright

from app.db import execute, fetch_one
from app.services.crypto import decrypt_payload

logger = logging.getLogger(__name__)

EXTRACT_JS = """
() => {
  const abs = (u) => {
    try { return new URL(u, location.href).href; } catch { return null; }
  };
  const visible = (el) => {
    const st = window.getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || el.value || '').trim().slice(0, 120);

  const links = [];
  const seenHref = new Set();
  document.querySelectorAll('a[href]').forEach((a, idx) => {
    const href = abs(a.getAttribute('href'));
    if (!href || seenHref.has(href)) return;
    seenHref.add(href);
    links.push({
      kind: 'link',
      href,
      text: textOf(a),
      label: textOf(a) || href,
      selector: `a[href]:nth-of-type(${idx + 1})`,
      interactive: visible(a),
    });
  });

  const buttons = [];
  const btnNodes = document.querySelectorAll(
    'button, [role="button"], input[type="submit"], input[type="button"], a.btn, .btn'
  );
  btnNodes.forEach((el, idx) => {
    if (!visible(el)) return;
    let selector = el.tagName.toLowerCase();
    if (el.id) selector = `#${CSS.escape(el.id)}`;
    else if (el.getAttribute('data-testid')) selector = `[data-testid="${el.getAttribute('data-testid')}"]`;
    else if (el.getAttribute('aria-label')) selector = `${el.tagName.toLowerCase()}[aria-label="${el.getAttribute('aria-label')}"]`;
    else {
      const t = textOf(el);
      if (t && el.tagName.toLowerCase() === 'button') {
        selector = `button:has-text("${t.replace(/"/g, '\\\\"').slice(0, 40)}")`;
      } else {
        selector = `${el.tagName.toLowerCase()}:nth-of-type(${idx + 1})`;
      }
    }
    buttons.push({
      kind: el.tagName.toLowerCase() === 'input' ? 'input' : 'button',
      href: null,
      text: textOf(el),
      label: textOf(el) || selector,
      selector,
      interactive: true,
    });
  });

  const nav = [];
  document.querySelectorAll('nav a[href], [role="navigation"] a[href]').forEach((a, idx) => {
    const href = abs(a.getAttribute('href'));
    if (!href) return;
    nav.push({
      kind: 'nav',
      href,
      text: textOf(a),
      label: textOf(a) || href,
      selector: `nav a[href]:nth-of-type(${idx + 1})`,
      interactive: visible(a),
    });
  });

  return { links, buttons, nav, title: document.title || '', url: location.href };
}
"""


def _normalize_url(url: str) -> str:
    cleaned, _ = urldefrag(url)
    return cleaned.rstrip("/") or cleaned


def _same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return pa.scheme == pb.scheme and pa.netloc == pb.netloc


def _path_of(url: str, base: str) -> str:
    parsed = urlparse(url)
    base_p = urlparse(base)
    if parsed.netloc and parsed.netloc != base_p.netloc:
        return url
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return path


def _parse_meta(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


async def _maybe_login(
    page: Page,
    base_url: str,
    credentials: dict[str, Any] | None,
    site_meta: dict[str, Any],
) -> None:
    if not credentials or not credentials.get("username") or not credentials.get("password"):
        return
    login = site_meta.get("login") if isinstance(site_meta.get("login"), dict) else {}
    path = str(login.get("path") or "/sign-in")
    user_sel = str(login.get("username_selector") or 'input[placeholder="Enter your username"]')
    pass_sel = str(login.get("password_selector") or 'input[type="password"]')
    submit_sel = str(login.get("submit_selector") or 'button[type="submit"]')
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.fill(user_sel, str(credentials["username"]))
    await page.fill(pass_sel, str(credentials["password"]))
    await page.click(submit_sel)
    try:
        await page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass


async def _insert_item(
    discovery_id: int,
    *,
    kind: str,
    page_url: str,
    page_path: str,
    href: str | None,
    path: str | None,
    label: str | None,
    selector: str | None,
    text: str | None,
    interactive: bool,
    sort_order: int,
    meta: dict[str, Any] | None = None,
) -> None:
    await execute(
        """
        INSERT INTO discovery_items (
            discovery_id, kind, page_url, page_path, href, path, label, selector, text,
            interactive, selected, meta, sort_order
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE,%s,%s)
        """,
        (
            discovery_id,
            kind,
            page_url,
            page_path,
            href,
            path,
            (label or "")[:300] or None,
            (selector or "")[:500] or None,
            (text or "")[:300] or None,
            interactive,
            json.dumps(meta or {}, ensure_ascii=False),
            sort_order,
        ),
    )


async def execute_discovery(discovery_id: int) -> None:
    row = await fetch_one("SELECT * FROM discoveries WHERE id = %s", (discovery_id,))
    if row is None:
        return

    base_url = str(row["base_url"]).rstrip("/")
    max_pages = int(row["max_pages"] or 40)
    max_depth = int(row["max_depth"] or 3)
    same_origin_only = bool(row["same_origin_only"])
    do_login = bool(row["do_login"])

    site_meta: dict[str, Any] = {}
    if row.get("site_id"):
        site = await fetch_one("SELECT * FROM sites WHERE id = %s", (row["site_id"],))
        if site:
            site_meta = _parse_meta(site.get("meta"))

    credentials: dict[str, Any] | None = None
    if row.get("credentials_id"):
        cred = await fetch_one("SELECT * FROM credentials WHERE id = %s", (row["credentials_id"],))
        if cred:
            credentials = decrypt_payload(cred["payload_encrypted"])

    await execute(
        "UPDATE discoveries SET status = 'running', started_at = NOW(), error_summary = NULL WHERE id = %s",
        (discovery_id,),
    )
    await execute("DELETE FROM discovery_items WHERE discovery_id = %s", (discovery_id,))

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()
    start = _normalize_url(base_url + "/")
    queue.append((start, 0))

    pages_count = 0
    links_count = 0
    buttons_count = 0
    sort_order = 0
    seen_item_keys: set[str] = set()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()

            if do_login:
                await _maybe_login(page, base_url, credentials, site_meta)

            while queue and pages_count < max_pages:
                url, depth = queue.popleft()
                norm = _normalize_url(url)
                if norm in visited:
                    continue
                if same_origin_only and not _same_origin(norm, base_url):
                    continue
                visited.add(norm)
                pages_count += 1

                try:
                    await page.goto(norm, wait_until="domcontentloaded", timeout=45000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                except Exception as exc:
                    logger.warning("discovery goto failed %s: %s", norm, exc)
                    continue

                current = _normalize_url(page.url)
                page_path = _path_of(current, base_url)
                try:
                    extracted = await page.evaluate(EXTRACT_JS)
                except Exception as exc:
                    logger.warning("extract failed on %s: %s", current, exc)
                    continue

                for group_name in ("links", "nav", "buttons"):
                    for raw in extracted.get(group_name) or []:
                        kind = str(raw.get("kind") or "link")
                        href = raw.get("href")
                        path = _path_of(href, base_url) if href else None
                        key = f"{kind}|{path or ''}|{raw.get('selector') or ''}|{raw.get('text') or ''}"
                        if key in seen_item_keys:
                            continue
                        seen_item_keys.add(key)
                        sort_order += 1
                        interactive = bool(raw.get("interactive", True))
                        await _insert_item(
                            discovery_id,
                            kind=kind if kind in ("link", "button", "input", "nav") else "link",
                            page_url=current,
                            page_path=page_path,
                            href=href,
                            path=path,
                            label=raw.get("label"),
                            selector=raw.get("selector"),
                            text=raw.get("text"),
                            interactive=interactive,
                            sort_order=sort_order,
                            meta={"from": group_name, "page_title": extracted.get("title")},
                        )
                        if kind in ("link", "nav"):
                            links_count += 1
                        else:
                            buttons_count += 1

                        if (
                            href
                            and depth < max_depth
                            and same_origin_only
                            and _same_origin(href, base_url)
                        ):
                            n = _normalize_url(href)
                            # skip non-http and likely assets
                            if n.startswith("http") and not re.search(
                                r"\.(png|jpe?g|gif|svg|css|js|ico|pdf|zip|woff2?)($|\?)",
                                n,
                                re.I,
                            ):
                                if n not in visited:
                                    queue.append((n, depth + 1))

            await context.close()
            await browser.close()

        summary = {
            "pages_visited": pages_count,
            "links": links_count,
            "buttons": buttons_count,
            "items": sort_order,
        }
        await execute(
            """
            UPDATE discoveries
            SET status = 'completed', finished_at = NOW(), summary_json = %s
            WHERE id = %s
            """,
            (json.dumps(summary), discovery_id),
        )
    except Exception as exc:
        logger.exception("discovery %s failed", discovery_id)
        await execute(
            """
            UPDATE discoveries
            SET status = 'failed', finished_at = NOW(), error_summary = %s
            WHERE id = %s
            """,
            (f"{type(exc).__name__}: {exc}"[:2000], discovery_id),
        )


def selected_items_to_pages(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group selected discovery items into Builder-like pages."""
    pages_map: dict[str, dict[str, Any]] = {}
    for item in items:
        kind = item.get("kind")
        if kind in ("link", "nav"):
            path = item.get("path") or item.get("href")
            if not path:
                continue
            # prefer relative path
            if str(path).startswith("http"):
                path = urlparse(str(path)).path or "/"
            key = str(path)
            if key not in pages_map:
                pages_map[key] = {
                    "title": item.get("label") or item.get("text") or key,
                    "path": key,
                    "assert_text": None,
                    "screenshot": True,
                    "buttons": [],
                }
        elif kind in ("button", "input"):
            page_path = item.get("page_path") or "/"
            if page_path not in pages_map:
                pages_map[page_path] = {
                    "title": page_path,
                    "path": page_path,
                    "assert_text": None,
                    "screenshot": True,
                    "buttons": [],
                }
            pages_map[page_path]["buttons"].append(
                {
                    "label": item.get("label"),
                    "text": item.get("text"),
                    "selector": item.get("selector"),
                    "wait_ms": 1000,
                }
            )
    return list(pages_map.values())

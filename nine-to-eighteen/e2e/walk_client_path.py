"""Клиентский путь UI 9to18: обход разделов, тестовые данные, очистка, отчёт.

Два прохода по витрине (плашки с /api/site/apps), блогам и кабинету.
На первом проходе скрипт добавляет только помеченные данные.
На втором удаляет их же и снимает экран после каждого шага.

Отчёт: nine-to-eighteen/e2e/reports/<дата-время>/index.html

Запуск из корня репозитория (UI на :8200, site-api, resume-api, portfolio-api):

    python -m pip install -r nine-to-eighteen/e2e/requirements.txt
    python -m playwright install chromium
    python nine-to-eighteen/e2e/walk_client_path.py

Переменные:
    E2E_BASE_URL          по умолчанию http://127.0.0.1:8200
    E2E_USER / E2E_PASSWORD   готовый аккаунт; иначе скрипт регистрирует свой
    E2E_HEADED=1          окно браузера
    E2E_SUBMIT_CONTACT=1  отправить форму связи (в UI сообщения не удаляются)
    E2E_ALLOW_REMOTE=1    разрешить хост кроме localhost
    E2E_ALLOW_NEW_HANDLE=1  создать адрес портфолио у уже существующего аккаунта

Супер-админ дополнительно создаёт плашку и черновик статьи, затем удаляет их.
Пароль, карту обучения, спотлайт и чужие сервисы скрипт не меняет.
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).resolve().parents[2]
REPORTS_ROOT = Path(__file__).resolve().parent / "reports"
MARKER_CITY = "E2E"
VIEWPORT_ONLY = {"/game/bowl", "/game/code", "/game/sql", "/game/git"}

ACCOUNT_EXTRA: list[tuple[str, str, str, str]] = [
    ("account-study", "/account?section=study", "Учёба", "visit"),
    ("account-learn", "/account?section=learn", "Learn в кабинете", "visit"),
    ("account-map", "/account?section=learning-map", "Карта в кабинете", "visit"),
    ("account-resume", "/account?section=hh-resume", "Резюме в кабинете", "visit"),
    ("account-portfolio", "/account?section=portfolio", "Портфолио в кабинете", "visit"),
    ("account-contact", "/account?section=contact", "Форма связи", "contact"),
    ("account-password", "/account?section=password", "Смена пароля", "password"),
]


@dataclass
class Route:
    slug: str
    path: str | None
    title: str
    kind: str
    external: str = ""


@dataclass
class Created:
    username: str = ""
    email: str = ""
    registered: bool = False
    profile_city_before: str | None = None
    profile_saved: bool = False
    resume_name: str = ""
    portfolio_case: str = ""
    portfolio_handle: str = ""
    portfolio_handle_created: bool = False
    resume_id: str = ""
    app_slug: str = ""
    post_slug: str = ""
    is_admin: bool = False
    contact_submitted: bool = False


@dataclass
class Step:
    phase: str
    slug: str
    title: str
    status: str
    url: str
    note: str
    image: str


@dataclass
class Report:
    root: Path
    steps: list[Step] = field(default_factory=list)
    failures: int = 0

    def __post_init__(self) -> None:
        (self.root / "screenshots").mkdir(parents=True, exist_ok=True)

    async def snap(
        self,
        page: Page,
        phase: str,
        slug: str,
        title: str,
        *,
        status: str = "ok",
        note: str = "",
        full_page: bool = True,
    ) -> None:
        index = len(self.steps) + 1
        filename = f"{index:02d}-{phase}-{slug}.png"
        target = self.root / "screenshots" / filename
        try:
            await page.screenshot(path=str(target), full_page=full_page, timeout=60_000)
        except Exception as exc:
            try:
                await page.screenshot(path=str(target), full_page=False, timeout=15_000)
                note = f"{note} · снимок окна ({exc})".strip(" ·")
            except Exception as shot_exc:
                filename = ""
                status = "fail" if status == "ok" else status
                note = f"{note} · нет снимка: {shot_exc}".strip(" ·")
        if status == "fail":
            self.failures += 1
        url = ""
        try:
            url = page.url
        except Exception:
            url = ""
        self.steps.append(
            Step(
                phase=phase,
                slug=slug,
                title=title,
                status=status,
                url=url,
                note=note,
                image=f"screenshots/{filename}" if filename else "",
            )
        )
        self.flush()

    async def run(
        self,
        page: Page,
        phase: str,
        slug: str,
        title: str,
        action: Callable[[], Awaitable[str]],
        *,
        full_page: bool = True,
    ) -> bool:
        status = "ok"
        note = ""
        try:
            note = await action() or ""
        except Exception as exc:
            status = "fail"
            note = f"{type(exc).__name__}: {exc}"
        await self.snap(
            page,
            phase,
            slug,
            title,
            status=status,
            note=note,
            full_page=full_page,
        )
        return status == "ok"

    def flush(self) -> None:
        payload = [asdict(step) for step in self.steps]
        (self.root / "steps.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        failed = sum(1 for step in self.steps if step.status == "fail")
        skipped = sum(1 for step in self.steps if step.status == "skip")
        passed = sum(1 for step in self.steps if step.status == "ok")
        rows = []
        for step in self.steps:
            image = (
                f'<a href="{html.escape(step.image)}"><img src="{html.escape(step.image)}" alt=""></a>'
                if step.image
                else ""
            )
            rows.append(
                "<article class='step'>"
                f"<header><span class='{html.escape(step.status)}'>{html.escape(step.status)}</span> "
                f"<strong>{html.escape(step.phase)}</strong> · {html.escape(step.title)}</header>"
                f"<p class='url'>{html.escape(step.url)}</p>"
                f"<p>{html.escape(step.note)}</p>"
                f"{image}</article>"
            )
        document = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Клиентский путь 9to18</title>
  <style>
    body {{ font: 16px/1.45 "Segoe UI", sans-serif; margin: 24px; background: #f6f7f9; color: #1c2430; }}
    h1 {{ margin-bottom: 0.2rem; }}
    .totals span {{ display: inline-block; margin-right: 1rem; }}
    article {{ background: #fff; border: 1px solid #d9dee7; border-radius: 10px; padding: 12px 14px; margin: 12px 0; }}
    img {{ max-width: 100%; border: 1px solid #e4e8ef; border-radius: 6px; }}
    .url {{ color: #526070; font-size: 0.9rem; word-break: break-all; }}
    .ok {{ color: #0f7b45; }} .fail {{ color: #b42318; }} .skip {{ color: #8a5a00; }}
  </style>
</head>
<body>
  <h1>Клиентский путь UI 9to18</h1>
  <p class="totals"><span class="ok">ok {passed}</span><span class="fail">fail {failed}</span><span class="skip">skip {skipped}</span></p>
  {''.join(rows)}
</body>
</html>
"""
        (self.root / "index.html").write_text(document, encoding="utf-8")


def assert_local_target(base_url: str) -> None:
    host = (urlparse(base_url).hostname or "").lower()
    if host in {"127.0.0.1", "localhost"}:
        return
    if os.getenv("E2E_ALLOW_REMOTE") == "1":
        return
    raise SystemExit(
        "Скрипт пишет тестовые данные. Для хоста кроме localhost задайте E2E_ALLOW_REMOTE=1."
    )


def load_apps(base_url: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(f"{base_url.rstrip('/')}/api/site/apps")
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)
    apps = payload.get("apps")
    if not isinstance(apps, list):
        return []
    return [item for item in apps if isinstance(item, dict)]


def kind_for_path(path: str) -> str:
    if path == "/account":
        return "profile"
    if path == "/game/hh-resume":
        return "resume"
    if path == "/game/portfolio":
        return "portfolio"
    return "visit"


def _path_only(href: str) -> str:
    return href.split("?", 1)[0].rstrip("/") or "/"


def index_tiles(hrefs: list[str], apps: list[dict[str, Any]]) -> dict[str, str]:
    """Сопоставляет кликабельную плашку на витрине со slug сервиса."""
    found: dict[str, str] = {}
    slugs = {str(app.get("slug") or "") for app in apps}
    for href in hrefs:
        if not href:
            continue
        path = _path_only(href)
        for app in apps:
            slug = str(app.get("slug") or "")
            app_path = _path_only(str(app.get("appPath") or ""))
            external = str(app.get("externalHref") or "").rstrip("/")
            if path in {f"/app/{slug}", f"/blog/{slug}", f"/game/{slug}"} or (
                app_path and path == app_path
            ):
                found[slug] = href
            elif external and href.rstrip("/") == external:
                found[slug] = href
        if path.startswith("/app/"):
            slug = path.split("/")[-1]
            if slug in slugs:
                found.setdefault(slug, href)
    return found


def build_routes(apps: list[dict[str, Any]], tiles: dict[str, str] | None = None) -> list[Route]:
    tiles = tiles or {}
    routes = [Route("home", "/", "Витрина", "visit")]
    seen_paths = {"/"}
    for app in apps:
        if app.get("isVisible") is False:
            continue
        slug = str(app.get("slug") or "").strip()
        title = str(app.get("title") or slug)
        app_path = str(app.get("appPath") or "").strip()
        external = str(app.get("externalHref") or "").strip()
        tile = tiles.get(slug, "")
        if tile.startswith(("http://", "https://")):
            routes.append(Route(f"tile-{slug}", None, title, "external", external=tile))
        elif tile.startswith("/") and _path_only(tile) not in seen_paths:
            routes.append(Route(f"tile-{slug}", tile, f"{title} · плашка", "visit"))
            seen_paths.add(_path_only(tile))
        elif not tile and external:
            routes.append(Route(f"tile-{slug}", None, title, "external", external=external))
        if app_path.startswith("/") and not app_path.startswith("//") and _path_only(app_path) not in seen_paths:
            routes.append(Route(f"service-{slug}", app_path, title, kind_for_path(app_path)))
            seen_paths.add(_path_only(app_path))
        routes.append(Route(f"blog-{slug}", f"/blog/{slug}", f"Блог · {title}", "blog"))
    if not any(route.kind == "profile" for route in routes):
        routes.append(Route("account-profile", "/account", "Профиль", "profile"))
    for slug, path, title, kind in ACCOUNT_EXTRA:
        routes.append(Route(slug, path, title, kind))
    return routes


def wants_full_page(path: str | None) -> bool:
    if not path:
        return True
    clean = path.split("?", 1)[0]
    return clean not in VIEWPORT_ONLY


async def visible_error(page: Page) -> str:
    locator = page.locator(".learn-admin-error, .contact-form-error")
    count = await locator.count()
    parts: list[str] = []
    for index in range(count):
        item = locator.nth(index)
        if not await item.is_visible():
            continue
        text = (await item.inner_text()).strip()
        if text:
            parts.append(text)
    return "; ".join(parts)


async def open_path(page: Page, base_url: str, path: str) -> None:
    await page.goto(f"{base_url.rstrip('/')}{path}", wait_until="domcontentloaded", timeout=45_000)
    try:
        await page.wait_for_selector(
            "h1, .home-title, .learn-title, .bowl-screen",
            timeout=15_000,
        )
    except Exception:
        return
    if path.split("?", 1)[0] == "/game/bowl":
        try:
            await page.wait_for_function(
                """() => {
                  const text = document.body.innerText || '';
                  return text.includes('Играть') || text.includes('Загрузка Bowl') || text.includes('Bowl');
                }""",
                timeout=12_000,
            )
        except Exception:
            return


async def accept_dialog(dialog) -> None:  # type: ignore[no-untyped-def]
    await dialog.accept()


async def authenticate(page: Page, base_url: str, created: Created, report: Report) -> bool:
    username = os.getenv("E2E_USER", "").strip()
    password = os.getenv("E2E_PASSWORD", "").strip()
    if username and password:
        created.username = username
        created.registered = False

        async def login() -> str:
            await open_path(page, base_url, "/login")
            await page.get_by_label("Email или username").fill(username)
            await page.get_by_label("Пароль", exact=True).fill(password)
            await page.get_by_role("button", name="Войти").click()
            await page.wait_for_url(re.compile(r"/account"), timeout=20_000)
            error = await visible_error(page)
            if error and "/account" not in page.url:
                raise RuntimeError(error)
            return f"вход {username}"

        return await report.run(page, "seed", "login", "Вход", login)

    stamp = secrets.token_hex(4)
    created.username = f"e2e_{stamp}"
    created.email = f"e2e_{stamp}@example.com"
    created.registered = True
    password = f"E2e-{stamp}-a1"
    (report.root / "account.txt").write_text(
        f"username={created.username}\nemail={created.email}\npassword={password}\n",
        encoding="utf-8",
    )

    async def register() -> str:
        await open_path(page, base_url, "/register")
        await page.get_by_label("Email", exact=True).fill(created.email)
        await page.get_by_label(re.compile(r"^Username")).fill(created.username)
        await page.get_by_label("Пароль", exact=True).fill(password)
        await report.snap(page, "seed", "register-form", "Форма регистрации", note=created.email)
        await page.get_by_role("button", name="Создать аккаунт").click()
        try:
            await page.wait_for_url(re.compile(r"/account"), timeout=20_000)
        except Exception as exc:
            error = await visible_error(page)
            raise RuntimeError(error or str(exc)) from exc
        return f"зарегистрирован {created.username}"

    return await report.run(page, "seed", "register", "Регистрация", register)


async def detect_admin(page: Page, base_url: str, created: Created) -> list[Route]:
    await open_path(page, base_url, "/account")
    admin_link = page.get_by_role("link", name="Супер-админ сайта")
    created.is_admin = await admin_link.count() > 0
    extra: list[Route] = []
    if created.is_admin:
        extra.append(Route("admin-site", "/account?section=site-admin", "Супер-админ сайта", "admin"))
        extra.append(Route("admin-learn", "/account?section=learn-cms", "Learn · контент", "visit"))
    links = page.locator("a.admin-jump-nav-link")
    count = await links.count()
    for index in range(count):
        href = await links.nth(index).get_attribute("href") or ""
        if "section=app:" not in href and "section=app%3A" not in href:
            continue
        label = (await links.nth(index).inner_text()).strip() or href
        extra.append(Route(f"owned-{index}", href, f"Сервис · {label}", "visit"))
    return extra


async def seed_profile(page: Page, created: Created, marker: str) -> str:
    await page.get_by_role("button", name="Сохранить анкету").wait_for(timeout=15_000)
    city = page.get_by_label("Город", exact=True)
    created.profile_city_before = await city.input_value()
    await city.fill(f"{MARKER_CITY} {marker}")
    await page.get_by_role("button", name="Сохранить анкету").click()
    await page.get_by_text("Анкета сохранена").wait_for(timeout=15_000)
    created.profile_saved = True
    return f"город = {MARKER_CITY} {marker}"


async def cleanup_profile(page: Page, created: Created) -> str:
    if not created.profile_saved:
        return "анкету не меняли"
    await page.get_by_role("button", name="Сохранить анкету").wait_for(timeout=15_000)
    city = page.get_by_label("Город", exact=True)
    await city.fill(created.profile_city_before or "")
    await page.get_by_role("button", name="Сохранить анкету").click()
    await page.get_by_text("Анкета сохранена").wait_for(timeout=15_000)
    created.profile_saved = False
    return "город возвращён"


async def seed_resume(page: Page, base_url: str, created: Created, marker: str) -> str:
    await page.get_by_role("button", name="Создать резюме").click()
    try:
        await page.wait_for_url(re.compile(r"/game/hh-resume/[^/]+/"), timeout=20_000)
    except Exception as exc:
        error = await visible_error(page)
        raise RuntimeError(error or "не открылось созданное резюме") from exc
    current = page.url.split("?", 1)[0].rstrip("/")
    resume_root = current[: -len("/path")] if current.endswith("/path") else current
    created.resume_id = resume_root.rstrip("/").split("/")[-1]
    edit_path = f"/game/hh-resume/{created.resume_id}/edit"
    await open_path(page, base_url, edit_path)
    name = page.get_by_label("Название версии")
    await name.wait_for(timeout=20_000)
    created.resume_name = f"E2E {marker}"
    await name.fill(created.resume_name)
    await page.locator("form.hh-resume-form").get_by_role("button", name="Сохранить", exact=True).click()
    await page.get_by_text("Изменения сохранены").wait_for(timeout=20_000)
    return created.resume_name


async def cleanup_resume(page: Page, base_url: str, created: Created) -> str:
    if not created.resume_name and created.resume_id and created.registered:
        await open_path(page, base_url, f"/game/hh-resume/{created.resume_id}/edit")
        created.resume_name = (await page.get_by_label("Название версии").input_value()).strip()
        await open_path(page, base_url, "/game/hh-resume")
    if not created.resume_name:
        return "резюме не создавали"
    card = page.locator("li.hh-resume-version-card").filter(has_text=created.resume_name)
    await card.first.wait_for(timeout=15_000)
    await card.get_by_role("button", name="Удалить").click()
    await page.get_by_text("Удалено", exact=True).wait_for(timeout=15_000)
    await card.wait_for(state="detached", timeout=15_000)
    name = created.resume_name
    created.resume_name = ""
    created.resume_id = ""
    return f"удалено {name}"


async def seed_portfolio(page: Page, created: Created, marker: str) -> str:
    handle = page.get_by_label("Адрес страницы")
    await handle.wait_for(timeout=15_000)
    add_case = page.get_by_role("button", name=re.compile(r"^Добавить материал"))
    await add_case.wait_for(timeout=15_000)
    if await add_case.is_disabled():
        if not created.registered and os.getenv("E2E_ALLOW_NEW_HANDLE") != "1":
            raise RuntimeError(
                "страница портфолио ещё не сохранена; для чужого аккаунта задайте E2E_ALLOW_NEW_HANDLE=1"
            )
        if not (await handle.input_value()).strip():
            await handle.fill(marker.lower())
        publish = page.get_by_label("Опубликовать страницу")
        if await publish.is_checked():
            await publish.uncheck()
        await page.get_by_role("button", name="Сохранить страницу").click()
        await page.get_by_text(re.compile("Черновик сохранён|Страница опубликована")).wait_for(
            timeout=15_000
        )
        error = await visible_error(page)
        if error:
            raise RuntimeError(error)
        created.portfolio_handle_created = True
    created.portfolio_handle = (await handle.input_value()).strip()
    add_case = page.get_by_role("button", name=re.compile(r"^Добавить материал"))
    enabled = False
    for _ in range(20):
        if not await add_case.is_disabled():
            enabled = True
            break
        await page.wait_for_timeout(250)
    if not enabled:
        raise RuntimeError("кнопка «Добавить материал» недоступна после сохранения адреса")
    await add_case.click()
    editor = page.locator("form.portfolio-material").filter(has=page.get_by_role("button", name="Отмена"))
    created.portfolio_case = f"E2E кейс {marker}"
    await editor.get_by_label("Название", exact=True).fill(created.portfolio_case)
    await editor.get_by_label("Краткое описание", exact=True).fill("Проверка клиентского пути")
    await editor.get_by_label("Ссылка", exact=True).fill("https://example.com/e2e")
    await editor.get_by_role("button", name="Сохранить материал").click()
    await page.get_by_text("Материал добавлен").wait_for(timeout=15_000)
    return created.portfolio_case


async def cleanup_portfolio(page: Page, created: Created) -> str:
    if not created.portfolio_case:
        return "кейс не создавали"
    editor = page.locator("article.portfolio-tile").filter(has_text=created.portfolio_case)
    await editor.first.wait_for(timeout=15_000)
    await editor.get_by_role("button", name="Удалить", exact=True).click()
    await page.get_by_text("Материал удалён").wait_for(timeout=15_000)
    name = created.portfolio_case
    created.portfolio_case = ""
    return f"удалён {name}"


async def seed_contact(page: Page, created: Created, marker: str) -> str:
    await page.get_by_placeholder("Как к вам обращаться").fill(f"E2E {marker}")
    await page.get_by_placeholder("you@example.com").fill(created.email or f"{marker}@example.com")
    await page.get_by_placeholder("Вопрос, предложение или проблема").fill(
        f"E2E {marker}: проверка формы связи"
    )
    if os.getenv("E2E_SUBMIT_CONTACT") != "1":
        return "форма заполнена и не отправлена: в UI нет удаления сообщений"
    await page.get_by_role("button", name="Отправить").click()
    await page.get_by_text("Сообщение отправлено").wait_for(timeout=15_000)
    created.contact_submitted = True
    return "сообщение отправлено; удалить его в UI нельзя, на очистке статус станет done если есть права"


async def cleanup_contact(page: Page, base_url: str, created: Created, marker: str) -> str:
    if not created.contact_submitted:
        return "черновик не сохранялся"
    if not created.is_admin:
        return "сообщение осталось в общей ленте: текущий аккаунт не супер-админ"
    await open_path(page, base_url, "/account?section=site-admin")
    row = page.locator("li.learn-admin-row").filter(has_text=f"E2E {marker}")
    await row.first.wait_for(timeout=15_000)
    await row.get_by_role("button", name="done", exact=True).click()
    created.contact_submitted = False
    return "статус сообщения: done"


async def seed_admin(page: Page, base_url: str, created: Created, marker: str, report: Report) -> str:
    form = page.locator("form").filter(has=page.get_by_role("button", name="Создать плашку"))
    await form.wait_for(timeout=15_000)
    created.app_slug = marker.lower()
    await form.get_by_label("Slug", exact=True).fill(created.app_slug)
    await form.get_by_label("Название", exact=True).fill(f"E2E {marker}")
    await form.get_by_role("button", name="Создать плашку").click()
    await page.get_by_text("Плашка создана").wait_for(timeout=15_000)
    await report.snap(page, "seed", "admin-tile", "Плашка создана", note=created.app_slug)

    await open_path(page, base_url, f"/admin/apps/{created.app_slug}")
    await page.get_by_role("button", name="Новая статья").click()
    post_form = page.locator("form").filter(has=page.get_by_role("button", name="Сохранить статью"))
    created.post_slug = "e2e-note"
    await post_form.get_by_label("Slug", exact=True).fill(created.post_slug)
    await post_form.get_by_label("Заголовок", exact=True).fill(f"E2E заметка {marker}")
    await post_form.get_by_role("checkbox", name="Опубликована").uncheck()
    await post_form.get_by_role("checkbox", name=re.compile("Единый формат")).uncheck()
    await post_form.get_by_label("Текст (markdown)").fill(
        f"Черновик клиентского прохода {marker}. Будет удалён."
    )
    await post_form.get_by_role("button", name="Сохранить статью").click()
    await page.get_by_text("Статья сохранена").wait_for(timeout=15_000)
    await report.snap(page, "seed", "admin-post", "Черновик статьи", note=created.post_slug)

    await open_path(page, base_url, f"/blog/{created.app_slug}")
    await report.snap(page, "seed", "admin-blog", "Блог тестовой плашки", note=created.app_slug)
    await open_path(page, base_url, "/")
    await report.snap(page, "seed", "home-with-tile", "Витрина с тестовой плашкой", note=created.app_slug)
    return created.app_slug


async def cleanup_admin(page: Page, base_url: str, created: Created, report: Report) -> str:
    if not created.app_slug:
        return "тестовую плашку не создавали"
    if created.post_slug:
        await open_path(page, base_url, f"/admin/apps/{created.app_slug}")
        row = page.locator("li.learn-admin-row").filter(has_text=created.post_slug)
        await row.first.wait_for(timeout=15_000)
        await row.get_by_role("button", name="Удалить").click()
        await page.get_by_text(f"Удалена статья {created.post_slug}").wait_for(timeout=15_000)
        await report.snap(page, "cleanup", "admin-post", "Статья удалена", note=created.post_slug)
        created.post_slug = ""
    await open_path(page, base_url, "/account?section=site-admin")
    row = page.locator("li.learn-admin-row").filter(has_text=created.app_slug)
    await row.first.wait_for(timeout=15_000)
    await row.get_by_role("button", name="Удалить").click()
    await page.get_by_text(f"Удалена: {created.app_slug}").wait_for(timeout=15_000)
    slug = created.app_slug
    created.app_slug = ""
    await report.snap(page, "cleanup", "admin-tile", "Плашка удалена", note=slug)
    await open_path(page, base_url, "/")
    await report.snap(page, "cleanup", "home-without-tile", "Витрина без тестовой плашки", note=slug)
    return f"удалена плашка {slug}"


async def mutate(page: Page, base_url: str, route: Route, phase: str, created: Created, marker: str, report: Report) -> str:
    if phase == "seed" and route.kind == "profile":
        return await seed_profile(page, created, marker)
    if phase == "cleanup" and route.kind == "profile":
        return await cleanup_profile(page, created)
    if phase == "seed" and route.kind == "resume":
        return await seed_resume(page, base_url, created, marker)
    if phase == "cleanup" and route.kind == "resume":
        return await cleanup_resume(page, base_url, created)
    if phase == "seed" and route.kind == "portfolio":
        return await seed_portfolio(page, created, marker)
    if phase == "cleanup" and route.kind == "portfolio":
        return await cleanup_portfolio(page, created)
    if phase == "seed" and route.kind == "contact":
        return await seed_contact(page, created, marker)
    if phase == "cleanup" and route.kind == "contact":
        return await cleanup_contact(page, base_url, created, marker)
    if phase == "seed" and route.kind == "admin":
        return await seed_admin(page, base_url, created, marker, report)
    if phase == "cleanup" and route.kind == "admin":
        return await cleanup_admin(page, base_url, created, report)
    if route.kind == "password":
        return "пароль не менялся"
    if route.kind == "external":
        return f"внешняя ссылка, переход не выполнялся: {route.external}"
    return ""


async def walk(
    page: Page,
    base_url: str,
    routes: list[Route],
    phase: str,
    created: Created,
    marker: str,
    report: Report,
) -> None:
    for route in routes:
        full_page = wants_full_page(route.path)

        async def visit(route: Route = route) -> str:
            if route.kind == "external":
                await open_path(page, base_url, "/")
                link = page.locator(f'a[href="{route.external}"]')
                if await link.count() == 0:
                    raise RuntimeError(f"на витрине нет ссылки {route.external}")
                await link.first.scroll_into_view_if_needed()
            elif route.path:
                await open_path(page, base_url, route.path)
                if route.kind == "blog" and "/blog/" not in page.url:
                    raise RuntimeError(
                        f"ждали {route.path}, открылся {page.url}. "
                        "В исходниках блог — /blog/:slug; запущенный ui-9to18 уводит этот адрес на главную."
                    )
            else:
                raise RuntimeError("у раздела нет пути")
            error = await visible_error(page)
            if error and route.kind != "visit":
                raise RuntimeError(error)
            return await mutate(page, base_url, route, phase, created, marker, report)

        await report.run(
            page,
            phase,
            route.slug,
            route.title,
            visit,
            full_page=full_page,
        )
        (report.root / "created.json").write_text(
            json.dumps(asdict(created), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


async def main() -> int:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8200").rstrip("/")
    assert_local_target(base_url)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    marker = f"e2e{stamp[-6:]}"
    report = Report(REPORTS_ROOT / stamp)
    created = Created()
    try:
        apps = load_apps(base_url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        report.failures += 1
        report.steps.append(
            Step("seed", "apps", "Список сервисов", "fail", f"{base_url}/api/site/apps", str(exc), "")
        )
        report.flush()
        print(f"Не удалось прочитать {base_url}/api/site/apps: {exc}", file=sys.stderr)
        print(report.root / "index.html")
        return 1

    headed = os.getenv("E2E_HEADED") == "1"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not headed)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="ru-RU")
        page = await context.new_page()
        page.on("dialog", accept_dialog)
        try:
            await open_path(page, base_url, "/")
            hrefs = await page.locator("a.section-tile, a.section-tile-external").evaluate_all(
                "els => els.map((el) => el.getAttribute('href'))"
            )
            routes = build_routes(apps, index_tiles([href for href in hrefs if href], apps))
            authed = await authenticate(page, base_url, created, report)
            if authed:
                routes.extend(await detect_admin(page, base_url, created))
                await walk(page, base_url, routes, "seed", created, marker, report)
                await walk(page, base_url, routes, "cleanup", created, marker, report)
            else:
                for route in routes:
                    if route.kind != "external":
                        route.kind = "visit"
                await walk(page, base_url, routes, "seed", created, marker, report)
        except Exception as exc:
            await report.snap(page, "seed", "aborted", "Остановка", status="fail", note=str(exc))
        finally:
            await context.close()
            await browser.close()
    print(report.root / "index.html")
    return 1 if report.failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc

"""Клиентский путь UI CopyParse: обход разделов, тестовые данные, очистка, отчёт.

Два прохода по меню (профиль, бренды, каналы, посты, библиотека, платформы, кабинет).
На первом проходе скрипт создаёт только помеченные записи.
На втором удаляет их и снимает экран после каждого шага.

Не публикует посты, не подключает Telegram/VK и не отправляет обратную связь:
в интерфейсе эти сообщения нельзя удалить.

Отчёт: ui-app/e2e/reports/<дата-время>/index.html

    python -m pip install -r ui-app/e2e/requirements.txt
    python -m playwright install chromium
    python ui-app/e2e/walk_client_path.py

Переменные:
    E2E_BASE_URL              по умолчанию http://127.0.0.1:8100
    E2E_USER / E2E_PASSWORD   готовый аккаунт; иначе скрипт регистрирует свой
    E2E_HEADED=1              окно браузера
    E2E_ALLOW_REMOTE=1        разрешить хост кроме localhost
    E2E_SUBMIT_FEEDBACK=1     отправить форму обратной связи
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import secrets
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import urlparse

from playwright.async_api import Page, async_playwright

REPORTS_ROOT = Path(__file__).resolve().parent / "reports"

# slug, path, title, kind
SECTIONS: list[tuple[str, str, str, str]] = [
    ("profile", "/profile", "Profile", "visit"),
    ("pricing", "/pricing", "Pricing", "visit"),
    ("about", "/about", "Справка", "visit"),
    ("brands", "/brands", "Brands", "brand"),
    ("channels", "/channels", "Channels", "visit"),
    ("inbox", "/inbox", "Inbox", "visit"),
    ("posts", "/posts", "Posts", "visit"),
    ("library", "/library", "Library", "library"),
    ("calendar", "/calendar", "Content Calendar", "visit"),
    ("analytics", "/analytics", "Analytics", "visit"),
    ("competitors", "/competitors", "Competitors", "visit"),
    ("automations", "/automations", "Automations", "automation"),
    ("telegram", "/telegram", "Telegram", "visit"),
    ("vkontakte", "/vkontakte", "VKontakte", "visit"),
    ("instagram", "/instagram", "Instagram", "visit"),
    ("threads", "/threads", "Threads", "visit"),
    ("wordpress", "/wordpress", "WordPress", "visit"),
    ("dzen", "/dzen", "Дзен", "visit"),
    ("twitter", "/twitter", "Twitter", "visit"),
    ("custom-url", "/custom-url", "Custom URL", "visit"),
    ("team", "/team", "Workspace", "workspace"),
    ("feedback", "/feedback", "Обратная связь", "feedback"),
    ("next", "/next", "Roadmap", "visit"),
    ("onboarding", "/onboarding", "Onboarding", "visit"),
]


@dataclass
class Route:
    slug: str
    path: str
    title: str
    kind: str


@dataclass
class Created:
    username: str = ""
    email: str = ""
    registered: bool = False
    brand_name: str = ""
    template_title: str = ""
    pack_title: str = ""
    automation_marker: str = ""
    is_admin: bool = False
    feedback_submitted: bool = False


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
    ) -> None:
        index = len(self.steps) + 1
        filename = f"{index:02d}-{phase}-{slug}.png"
        target = self.root / "screenshots" / filename
        try:
            await page.screenshot(path=str(target), full_page=True, timeout=60_000)
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
            Step(phase, slug, title, status, url, note, f"screenshots/{filename}" if filename else "")
        )
        self.flush()

    async def run(
        self,
        page: Page,
        phase: str,
        slug: str,
        title: str,
        action: Callable[[], Awaitable[str]],
    ) -> bool:
        status = "ok"
        note = ""
        try:
            note = await action() or ""
        except Exception as exc:
            status = "fail"
            note = f"{type(exc).__name__}: {exc}"
        await self.snap(page, phase, slug, title, status=status, note=note)
        return status == "ok"

    def flush(self) -> None:
        (self.root / "steps.json").write_text(
            json.dumps([asdict(step) for step in self.steps], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        passed = sum(1 for step in self.steps if step.status == "ok")
        failed = sum(1 for step in self.steps if step.status == "fail")
        skipped = sum(1 for step in self.steps if step.status == "skip")
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
                f"<p>{html.escape(step.note)}</p>{image}</article>"
            )
        document = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Клиентский путь CopyParse</title>
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
  <h1>Клиентский путь UI CopyParse</h1>
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


def section_routes() -> list[Route]:
    return [Route(slug, path, title, kind) for slug, path, title, kind in SECTIONS]


async def accept_dialog(dialog) -> None:  # type: ignore[no-untyped-def]
    await dialog.accept()


async def page_error(page: Page) -> str:
    locator = page.locator("[class*='bg-red-500']")
    count = await locator.count()
    parts: list[str] = []
    for index in range(min(count, 4)):
        item = locator.nth(index)
        if not await item.is_visible():
            continue
        text = " ".join((await item.inner_text()).split())
        if text:
            parts.append(text)
    return "; ".join(parts)


PLATFORM_PATHS = {
    "/telegram",
    "/vkontakte",
    "/instagram",
    "/threads",
    "/wordpress",
    "/dzen",
    "/twitter",
    "/custom-url",
}


async def sign_in(page: Page, base_url: str, username: str, password: str) -> None:
    for attempt in range(2):
        if "/sign-in" not in page.url:
            await page.goto(f"{base_url.rstrip('/')}/sign-in", wait_until="domcontentloaded")
        await page.get_by_placeholder("Enter your username").fill(username)
        await page.get_by_placeholder("Enter your password").fill(password)
        await page.get_by_role("button", name="Sign In").click()
        try:
            await page.wait_for_url(re.compile(r"/profile"), timeout=20_000)
            return
        except Exception:
            limited = page.get_by_text("Rate limit exceeded")
            if attempt == 0 and await limited.count():
                await page.wait_for_timeout(70_000)
                continue
            raise


async def click_section(page: Page, path: str) -> bool:
    href = "/inbox?mode=comments" if path == "/inbox" else path
    link = page.locator(f'a[href="{href}"]')
    if path in PLATFORM_PATHS and await link.count() == 0:
        toggle = page.get_by_role("button", name="Credentials")
        if await toggle.count():
            await toggle.first.click()
    if await link.count() == 0:
        return False
    await link.first.click()
    await page.wait_for_url(re.compile(rf"{re.escape(path)}(/|$|\?)|/onboarding"), timeout=15_000)
    return True


async def open_path(page: Page, base_url: str, path: str, *, username: str = "", password: str = "") -> None:
    async def settle() -> None:
        try:
            await page.wait_for_selector("h1, form", timeout=15_000)
        except Exception:
            return
        await page.wait_for_timeout(600)

    if "/sign-in" not in page.url and "/sign-up" not in page.url and await click_section(page, path):
        await settle()
    else:
        await page.goto(f"{base_url.rstrip('/')}{path}", wait_until="domcontentloaded", timeout=45_000)
        await settle()
    if "/sign-in" not in page.url or not username or not password:
        return
    await sign_in(page, base_url, username, password)
    if not await click_section(page, path):
        await page.goto(f"{base_url.rstrip('/')}{path}", wait_until="domcontentloaded", timeout=45_000)
    await settle()


async def authenticate(
    page: Page,
    base_url: str,
    created: Created,
    report: Report,
    secret: dict[str, str],
) -> bool:
    username = os.getenv("E2E_USER", "").strip()
    password = os.getenv("E2E_PASSWORD", "").strip()
    if username and password:
        created.username = username
        created.registered = False
        secret["password"] = password

        async def login() -> str:
            await open_path(page, base_url, "/sign-in")
            await page.get_by_placeholder("Enter your username").fill(username)
            await page.get_by_placeholder("Enter your password").fill(password)
            await page.get_by_role("button", name="Sign In").click()
            try:
                await page.wait_for_url(re.compile(r"/profile"), timeout=20_000)
            except Exception as exc:
                error = await page_error(page)
                raise RuntimeError(error or "после входа не открылся профиль") from exc
            return f"вход {username}"

        return await report.run(page, "seed", "login", "Вход", login)

    stamp = secrets.token_hex(4)
    created.username = f"e2e_{stamp}"
    created.email = f"e2e_{stamp}@example.com"
    created.registered = True
    password = f"E2e-{stamp}-a1"
    secret["password"] = password
    (report.root / "account.txt").write_text(
        f"username={created.username}\nemail={created.email}\npassword={password}\n",
        encoding="utf-8",
    )

    async def register() -> str:
        await open_path(page, base_url, "/sign-up")
        await page.get_by_placeholder("Choose a username").fill(created.username)
        await page.get_by_placeholder("Enter your email").fill(created.email)
        await page.get_by_placeholder("Create a password (min 8 characters)").fill(password)
        await page.get_by_placeholder("Confirm your password").fill(password)
        await report.snap(page, "seed", "register-form", "Форма регистрации", note=created.email)
        await page.get_by_role("button", name="Create Account").click()
        try:
            await page.wait_for_url(re.compile(r"/profile"), timeout=25_000)
        except Exception as exc:
            error = await page_error(page)
            raise RuntimeError(error or "после регистрации не открылся профиль") from exc
        return f"зарегистрирован {created.username}"

    return await report.run(page, "seed", "register", "Регистрация", register)


async def detect_admin(page: Page) -> list[Route]:
    link = page.get_by_role("link", name="Administration")
    if await link.count() == 0:
        return []
    return [
        Route("administration", "/administration", "Administration", "visit"),
        Route("polls", "/polls", "Polls", "visit"),
        Route("checks", "/checks", "Checks", "visit"),
    ]


async def seed_brand(page: Page, created: Created, marker: str) -> str:
    form = page.locator("form").filter(has=page.get_by_role("button", name="Create brand"))
    await form.wait_for(timeout=15_000)
    created.brand_name = f"E2E {marker}"
    await form.locator("input").first.fill(created.brand_name)
    await form.get_by_role("button", name="Create brand").click()
    await page.get_by_text("Бренд создан").wait_for(timeout=15_000)
    error = await page_error(page)
    if error:
        created.brand_name = ""
        raise RuntimeError(error)
    return created.brand_name


async def cleanup_brand(page: Page, created: Created) -> str:
    if not created.brand_name:
        return "бренд не создавали"
    row = page.locator("div.rounded-lg.border").filter(has_text=created.brand_name)
    target = row.first
    await target.wait_for(timeout=15_000)
    await target.get_by_role("button", name="Delete").click()
    await target.wait_for(state="detached", timeout=15_000)
    name = created.brand_name
    created.brand_name = ""
    return f"удалён {name}"


async def seed_library(page: Page, created: Created, marker: str) -> str:
    if not created.brand_name:
        raise RuntimeError("нет бренда — шаблон некуда сохранить")
    form = page.locator("form").filter(has=page.get_by_role("button", name="Сохранить")).first
    await form.wait_for(timeout=15_000)
    created.template_title = f"E2E {marker}"
    await form.locator("input").first.fill(created.template_title)
    await form.locator("textarea").fill("Проверка клиентского пути CopyParse")
    await form.get_by_role("button", name="Сохранить").click()
    await page.get_by_text("Шаблон сохранён").wait_for(timeout=15_000)

    await page.get_by_role("button", name="Media packs").click()
    pack_form = page.locator("form").filter(has=page.get_by_role("button", name="Сохранить"))
    await pack_form.wait_for(timeout=10_000)
    created.pack_title = f"E2E pack {marker}"
    await pack_form.locator("input").first.fill(created.pack_title)
    await pack_form.locator("textarea").fill(f"e2e/{marker}.txt")
    await pack_form.get_by_role("button", name="Сохранить").click()
    await page.get_by_text("Медиа-пакет сохранён").wait_for(timeout=15_000)
    error = await page_error(page)
    if error:
        raise RuntimeError(error)
    return f"{created.template_title}; {created.pack_title}"


async def cleanup_library(page: Page, created: Created) -> str:
    notes: list[str] = []
    if created.template_title:
        await page.get_by_role("button", name="Templates").click()
        row = page.locator("div.flex.items-start").filter(has_text=created.template_title)
        if await row.count() == 0:
            notes.append(f"{created.template_title} уже нет")
        else:
            target = row.first
            await target.get_by_role("button", name="Удалить").click()
            await target.wait_for(state="detached", timeout=15_000)
            notes.append(f"удалён шаблон {created.template_title}")
        created.template_title = ""
    if created.pack_title:
        await page.get_by_role("button", name="Media packs").click()
        row = page.locator("div.flex.items-start").filter(has_text=created.pack_title)
        target = row.first
        await target.wait_for(timeout=15_000)
        await target.get_by_role("button", name="Удалить").click()
        await target.wait_for(state="detached", timeout=15_000)
        notes.append(f"удалён пакет {created.pack_title}")
        created.pack_title = ""
    return "; ".join(notes) or "библиотеку не меняли"


async def seed_automation(page: Page, created: Created, marker: str) -> str:
    if not created.brand_name:
        raise RuntimeError("нет бренда — правило некуда сохранить")
    form = page.locator("form").filter(has=page.get_by_role("button", name="Create", exact=True))
    await form.wait_for(timeout=15_000)
    await form.locator("select").select_option("mention")
    await page.get_by_text("Keywords (comma-separated)").wait_for(timeout=10_000)
    marker_value = f"e2e{marker}"
    inputs = form.locator("input")
    await inputs.nth(0).fill(marker_value)
    await inputs.nth(1).fill(f"#{marker_value}")
    await form.get_by_role("button", name="Create", exact=True).click()
    card = page.locator("div.rounded.border").filter(has_text=marker_value)
    outcome = card.or_(page.get_by_text("Plan limit exceeded")).or_(page.get_by_text("Rate limit exceeded"))
    await outcome.first.wait_for(timeout=15_000)
    if await card.count() == 0:
        if await page.get_by_text("Plan limit exceeded").count():
            return "форма заполнена, правило не создано: на тарифе free автоматизации недоступны"
        if await page.get_by_text("Rate limit exceeded").count():
            return "форма заполнена, правило не создано: шлюз ограничил частоту запросов"
        return "форма заполнена, правило не появилось в списке"
    created.automation_marker = marker_value
    await card.first.get_by_role("button", name="Toggle").click()
    error = await page_error(page)
    if error:
        raise RuntimeError(error)
    return f"mention {created.automation_marker}, выключено"


async def cleanup_automation(page: Page, created: Created) -> str:
    if not created.automation_marker:
        return "правило не создавали"
    card = page.locator("div.rounded.border").filter(has_text=created.automation_marker)
    if await card.count() == 0:
        marker = created.automation_marker
        created.automation_marker = ""
        return f"правила {marker} в списке нет"
    target = card.first
    await target.wait_for(timeout=15_000)
    await target.get_by_role("button", name="Delete").click()
    await target.wait_for(state="detached", timeout=15_000)
    marker = created.automation_marker
    created.automation_marker = ""
    return f"удалено {marker}"


async def seed_workspace(page: Page, marker: str) -> str:
    if await page.get_by_text("Access denied").count():
        return "у роли guest форма workspace недоступна, запись не создавалась"
    field = page.get_by_placeholder("Workspace name")
    try:
        await field.wait_for(timeout=5_000)
    except Exception:
        return "формы создания workspace нет, запись не создавалась"
    await field.fill(f"E2E {marker}")
    return "имя заполнено и не отправлено: рабочее пространство в UI не удаляется"


async def seed_feedback(page: Page, created: Created, marker: str) -> str:
    await page.get_by_placeholder("Опишите проблему, предложение или вопрос...").fill(
        f"E2E {marker}: проверка формы, без отправки"
    )
    if os.getenv("E2E_SUBMIT_FEEDBACK") != "1":
        return "форма заполнена и не отправлена"
    await page.get_by_role("button", name="Отправить").click()
    await page.get_by_text("Сообщение отправлено").wait_for(timeout=15_000)
    created.feedback_submitted = True
    return "сообщение отправлено; удалить его может только администратор"


async def mutate(page: Page, route: Route, phase: str, created: Created, marker: str) -> str:
    if route.kind == "brand" and phase == "seed":
        return await seed_brand(page, created, marker)
    if route.kind == "brand" and phase == "cleanup":
        return "бренд удалим последним, после шаблона и правила"
    if route.kind == "library" and phase == "seed":
        return await seed_library(page, created, marker)
    if route.kind == "library" and phase == "cleanup":
        return await cleanup_library(page, created)
    if route.kind == "automation" and phase == "seed":
        return await seed_automation(page, created, marker)
    if route.kind == "automation" and phase == "cleanup":
        return await cleanup_automation(page, created)
    if route.kind == "workspace" and phase == "seed":
        return await seed_workspace(page, marker)
    if route.kind == "workspace" and phase == "cleanup":
        return "рабочее пространство не создавалось"
    if route.kind == "feedback" and phase == "seed":
        return await seed_feedback(page, created, marker)
    if route.kind == "feedback" and phase == "cleanup":
        if created.feedback_submitted:
            return "сообщение осталось в админке"
        return "черновик не сохранялся"
    if route.path == "/posts" and "/onboarding" in page.url:
        return "пост не создавался: нет подключённой площадки, открыт onboarding"
    if route.kind == "visit":
        return ""
    return ""


async def walk(
    page: Page,
    base_url: str,
    routes: list[Route],
    phase: str,
    created: Created,
    marker: str,
    report: Report,
    secret: dict[str, str],
) -> None:
    for route in routes:

        async def visit(route: Route = route) -> str:
            await open_path(
                page,
                base_url,
                route.path,
                username=created.username,
                password=secret["password"],
            )
            if "/sign-in" in page.url or "/sign-up" in page.url:
                raise RuntimeError("сессия не сохранилась")
            note = await mutate(page, route, phase, created, marker)
            if route.kind in {"brand", "library", "automation"} and phase == "seed":
                error = await page_error(page)
                if error and "Plan limit exceeded" not in error and "Rate limit exceeded" not in error:
                    raise RuntimeError(error)
            return note

        await report.run(page, phase, route.slug, route.title, visit)
        (report.root / "created.json").write_text(
            json.dumps(asdict(created), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        await page.wait_for_timeout(2000)

    if phase == "cleanup" and created.brand_name:
        async def remove_brand() -> str:
            await open_path(page, base_url, "/brands", username=created.username, password=secret["password"])
            return await cleanup_brand(page, created)

        await report.run(page, "cleanup", "brand-delete", "Удаление бренда", remove_brand)
        (report.root / "created.json").write_text(
            json.dumps(asdict(created), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def account_credentials(folder: Path) -> tuple[str, str]:
    username = ""
    password = ""
    account = folder / "account.txt"
    if not account.exists():
        return username, password
    for line in account.read_text(encoding="utf-8").splitlines():
        if line.startswith("username="):
            username = line.split("=", 1)[1].strip()
        elif line.startswith("password="):
            password = line.split("=", 1)[1].strip()
    return username, password


async def remove_previous_brands(page: Page, base_url: str, current_root: Path) -> None:
    """Удаляет бренды, оставшиеся после прерванных прогонов этого же скрипта."""
    if not REPORTS_ROOT.exists():
        return
    for folder in sorted(REPORTS_ROOT.iterdir()):
        if not folder.is_dir() or folder.resolve() == current_root.resolve():
            continue
        created_path = folder / "created.json"
        if not created_path.exists():
            continue
        try:
            saved = json.loads(created_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        brand_name = str(saved.get("brand_name") or "")
        if not brand_name:
            continue
        username, password = account_credentials(folder)
        if not username or not password:
            continue
        await page.evaluate(
            "() => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); }"
        )
        await page.goto(f"{base_url.rstrip('/')}/sign-in", wait_until="domcontentloaded")
        await sign_in(page, base_url, username, password)
        await open_path(page, base_url, "/brands", username=username, password=password)
        row = page.locator("div.rounded-lg.border").filter(has_text=brand_name)
        if await row.count() == 0:
            saved["brand_name"] = ""
            created_path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
            continue
        target = row.first
        await target.get_by_role("button", name="Delete").click()
        await target.wait_for(state="detached", timeout=15_000)
        saved["brand_name"] = ""
        created_path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")


async def main() -> int:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8100").rstrip("/")
    assert_local_target(base_url)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    marker = f"e2e{stamp[-6:]}"
    report = Report(REPORTS_ROOT / stamp)
    created = Created()
    secret: dict[str, str] = {"password": ""}
    routes = section_routes()
    headed = os.getenv("E2E_HEADED") == "1"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not headed)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
        page = await context.new_page()
        page.on("dialog", accept_dialog)
        try:
            authed = await authenticate(page, base_url, created, report, secret)
            if authed:
                routes.extend(await detect_admin(page))
                created.is_admin = any(route.slug == "administration" for route in routes)
                await walk(page, base_url, routes, "seed", created, marker, report, secret)
                await walk(page, base_url, routes, "cleanup", created, marker, report, secret)
                await remove_previous_brands(page, base_url, report.root)
            else:
                for route in routes:
                    route.kind = "visit"
                await walk(page, base_url, routes, "seed", created, marker, report, secret)
        except Exception as exc:
            await report.snap(page, "seed", "aborted", "Остановка", status="fail", note=str(exc))
        finally:
            await context.close()
            await browser.close()
    print(report.root / "index.html")
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

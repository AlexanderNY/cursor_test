"""Безопасный цикл CopyParse: регистрация, URL-канал, черновик, выход.

Канал указывает на example.com и остаётся с выключенным сбором.
Текст поста вводится в редактор и не отправляется: без авторизованной площадки
кнопка публикации недоступна. Живые Telegram, VK и остальные сети не подключаются.

Отчёт: ui-app/e2e/reports/cycle-<дата-время>/index.html

    python ui-app/e2e/session_cycle.py

Час простоя той же сессии: E2E_SOAK=1 python ui-app/e2e/soak_hour.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import walk_client_path as walk  # noqa: E402
from playwright.async_api import Page, async_playwright  # noqa: E402

SOURCE_URL = "https://example.com/e2e-copyparse"


async def add_url_channel(page: Page, title: str) -> str:
    form = page.locator("form").filter(has=page.get_by_role("button", name="Add", exact=True))
    await form.wait_for(timeout=15_000)
    await form.locator("select").nth(1).select_option("url")
    url_input = form.locator('input[type="url"]')
    await url_input.wait_for(timeout=10_000)
    await url_input.fill(SOURCE_URL)
    await form.get_by_placeholder("Smart-Lab map").fill(title)
    await form.get_by_role("button", name="Add", exact=True).click()
    row = page.locator("tr").filter(has_text=title)
    await row.first.wait_for(timeout=15_000)
    error = await walk.page_error(page)
    if error:
        raise RuntimeError(error)
    return title


async def open_channel_settings(page: Page, title: str) -> str:
    row = page.locator("tr").filter(has_text=title).first
    await row.get_by_role("link", name="Настроить").click()
    await page.wait_for_url(walk.re.compile(r"/channels/\d+"), timeout=15_000)
    collect = page.get_by_role("checkbox", name="Сбор включён (Collect)")
    await collect.wait_for(timeout=15_000)
    if await collect.is_checked():
        raise RuntimeError("сбор URL включился сам, страницу не сохраняем")
    return "сбор выключен, форма не сохранялась"


async def remove_channel(page: Page, title: str) -> str:
    row = page.locator("tr").filter(has_text=title).first
    await row.wait_for(timeout=15_000)
    await row.get_by_role("button", name="Remove").click()
    await row.wait_for(state="detached", timeout=15_000)
    return f"удалён канал {title}"


async def skip_onboarding_if_needed(page: Page) -> str:
    if "/onboarding" not in page.url:
        return ""
    await page.get_by_role("button", name="Skip (read-only mode)").click()
    await page.wait_for_url(walk.re.compile(r"/channels"), timeout=15_000)
    return "onboarding пропущен"


async def fill_draft(page: Page, marker: str) -> str:
    editor = page.locator("[contenteditable='true']").first
    await editor.wait_for(timeout=15_000)
    await editor.click()
    text = f"E2E черновик {marker}. Публикация не нажималась."
    await page.keyboard.type(text)
    notice = page.get_by_text("Нет каналов для публикации")
    if await notice.count() == 0:
        return "текст введён в редактор и не отправлен"
    return "текст введён в редактор и не отправлен: нет канала для публикации"


async def logout_and_probe(page: Page) -> str:
    await page.get_by_role("button", name="Logout").click()
    await page.wait_for_url(walk.re.compile(r"/sign-in"), timeout=20_000)
    result: dict[str, object] = {}
    for attempt in range(2):
        result = await page.evaluate(
            """async () => {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/auth/profile');
                return { token, status: response.status };
            }"""
        )
        status = int(result.get("status") or 0)
        if status != 429 or attempt == 1:
            break
        await page.wait_for_timeout(70_000)
    if result.get("token"):
        raise RuntimeError("после выхода access_token остался в браузере")
    status = int(result.get("status") or 0)
    if status != 401:
        raise RuntimeError(f"запрос профиля без токена вернул {status}")
    return "сессия закрыта, /api/auth/profile без токена → 401"


async def reopen_after_limit(
    page: Page,
    base_url: str,
    path: str,
    *,
    username: str,
    password: str,
) -> None:
    await walk.open_path(page, base_url, path, username=username, password=password)
    limited = await page.get_by_text("Rate limit exceeded").count()
    empty_brands = path == "/brands" and await page.get_by_text("Пока нет брендов").count()
    empty_channels = path == "/channels" and await page.get_by_text("Сначала создайте бренд").count()
    if not limited and not empty_brands and not empty_channels:
        return
    await page.wait_for_timeout(70_000)
    await page.reload(wait_until="domcontentloaded")
    try:
        await page.wait_for_selector("h1", timeout=15_000)
    except Exception:
        return


async def dwell(page: Page, base_url: str, created: walk.Created, secret: dict[str, str], report: walk.Report) -> None:
    minutes = int(os.getenv("E2E_SOAK_MINUTES", "60"))
    step_seconds = int(os.getenv("E2E_SOAK_STEP_SECONDS", "300"))
    deadline = time.monotonic() + minutes * 60
    round_index = 0
    while time.monotonic() < deadline:
        round_index += 1
        for path, title in (("/inbox", "Inbox"), ("/calendar", "Calendar"), ("/channels", "Channels")):
            await walk.open_path(
                page,
                base_url,
                path,
                username=created.username,
                password=secret["password"],
            )
            await report.snap(
                page,
                "soak",
                f"{title.lower()}-{round_index}",
                title,
                note=f"простой, круг {round_index}",
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        await page.wait_for_timeout(int(min(step_seconds, remaining) * 1000))


async def main() -> int:
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8100").rstrip("/")
    walk.assert_local_target(base_url)
    stamp = walk.datetime.now().strftime("%Y%m%d-%H%M%S")
    marker = f"e2e{stamp[-6:]}"
    report = walk.Report(walk.REPORTS_ROOT / f"cycle-{stamp}")
    created = walk.Created()
    secret: dict[str, str] = {"password": ""}
    channel_title = f"E2E url {marker}"
    headed = os.getenv("E2E_HEADED") == "1"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not headed)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
        page = await context.new_page()
        page.on("dialog", walk.accept_dialog)
        try:
            authed = await walk.authenticate(page, base_url, created, report, secret)
            if not authed:
                raise RuntimeError("не удалось войти")

            async def create_brand() -> str:
                await walk.open_path(page, base_url, "/brands", username=created.username, password=secret["password"])
                return await walk.seed_brand(page, created, marker)

            await report.run(page, "cycle", "brand", "Бренд", create_brand)
            (report.root / "created.json").write_text(
                walk.json.dumps(walk.asdict(created), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            async def create_channel() -> str:
                await walk.open_path(page, base_url, "/channels", username=created.username, password=secret["password"])
                return await add_url_channel(page, channel_title)

            await report.run(page, "cycle", "channel", "Канал URL", create_channel)

            async def inspect_channel() -> str:
                return await open_channel_settings(page, channel_title)

            await report.run(page, "cycle", "channel-settings", "Настройки канала", inspect_channel)

            async def draft() -> str:
                await walk.open_path(page, base_url, "/posts", username=created.username, password=secret["password"])
                skipped = await skip_onboarding_if_needed(page)
                if skipped:
                    await walk.open_path(page, base_url, "/posts", username=created.username, password=secret["password"])
                    skipped = f"{skipped}; {await skip_onboarding_if_needed(page)}".strip("; ")
                if "/onboarding" in page.url:
                    raise RuntimeError("после пропуска onboarding снова открыт мастер")
                note = await fill_draft(page, marker)
                return f"{skipped}; {note}".strip("; ")

            await report.run(page, "cycle", "draft", "Черновик", draft)

            for path, slug, title in (
                ("/inbox", "inbox", "Inbox"),
                ("/library", "library", "Library"),
                ("/calendar", "calendar", "Calendar"),
                ("/profile", "profile", "Profile"),
            ):

                async def visit(path: str = path) -> str:
                    await walk.open_path(
                        page,
                        base_url,
                        path,
                        username=created.username,
                        password=secret["password"],
                    )
                    if "/sign-in" in page.url:
                        raise RuntimeError("сессия не сохранилась")
                    return ""

                await report.run(page, "cycle", slug, title, visit)
                await page.wait_for_timeout(1500)

            if os.getenv("E2E_SOAK") == "1":
                await dwell(page, base_url, created, secret, report)

            async def drop_channel() -> str:
                await reopen_after_limit(
                    page,
                    base_url,
                    "/channels",
                    username=created.username,
                    password=secret["password"],
                )
                return await remove_channel(page, channel_title)

            await report.run(page, "cycle", "channel-delete", "Удаление канала", drop_channel)

            async def drop_brand() -> str:
                await reopen_after_limit(
                    page,
                    base_url,
                    "/brands",
                    username=created.username,
                    password=secret["password"],
                )
                return await walk.cleanup_brand(page, created)

            await report.run(page, "cycle", "brand-delete", "Удаление бренда", drop_brand)
            (report.root / "created.json").write_text(
                walk.json.dumps(walk.asdict(created), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            await report.run(page, "cycle", "logout", "Выход", lambda: logout_and_probe(page))
            await walk.remove_previous_brands(page, base_url, report.root)
        except Exception as exc:
            await report.snap(page, "cycle", "aborted", "Остановка", status="fail", note=str(exc))
        finally:
            await context.close()
            await browser.close()
    print(report.root / "index.html")
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

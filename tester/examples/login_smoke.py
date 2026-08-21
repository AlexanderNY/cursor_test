# Пример Playwright-скрипта.
# Обязательная точка входа: async def run(page, base_url, credentials, log)

async def run(page, base_url, credentials, log):
    await log(f"goto {base_url}/sign-in")
    await page.goto(f"{base_url.rstrip('/')}/sign-in", wait_until="domcontentloaded")
    username = credentials.get("username") or ""
    password = credentials.get("password") or ""
    if not username or not password:
        raise ValueError("password credentials required")
    await page.fill('input[placeholder="Enter your username"]', username)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await log(f"landed on {page.url}")

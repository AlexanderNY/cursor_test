"""Upsert newly seeded Learn posts into db_9to18. One-shot."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from database import init_db
from schema import SITE_ALL_TABLES, SITE_SCHEMA_PATCHES
from services.learn_service import learn_service

SLUGS = {
    "py-solid",
    "py-code-review",
    "py-sqlalchemy",
    "py-celery",
    "py-websockets",
    "fe-html-a11y",
    "fe-state-libraries",
    "fe-ui-testing",
    "fe-render-perf",
    "fe-storybook",
    "fe-microfront-next",
    "fe-openapi-client",
    "qa-playwright",
    "qa-reports-jira",
    "qa-mocks",
    "sa-jira-confluence",
    "sa-postman",
    "pm-discovery",
    "pm-acceptance",
    "pm-metrics",
    "sec-sast-dast-sca",
    "sec-threat-model",
    "sec-secure-review",
    "sec-csp-csrf",
    "sec-supply-chain",
    "sec-bug-bounty",
    "sec-sdlc",
    "sec-k8s",
}


async def main() -> None:
    await init_db(SITE_ALL_TABLES + SITE_SCHEMA_PATCHES)
    seed_path = Path(__file__).resolve().parent / "data" / "learn_seed.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    found = [item for item in seed if isinstance(item, dict) and item.get("slug") in SLUGS]
    missing = SLUGS - {item["slug"] for item in found}
    if missing:
        raise SystemExit(f"missing in seed: {sorted(missing)}")
    for item in found:
        saved = await learn_service.upsert_post(item)
        print(f"{saved['slug']} {saved.get('episode')} {saved.get('rubricId')}")
    print(f"upserted {len(found)}")


if __name__ == "__main__":
    asyncio.run(main())

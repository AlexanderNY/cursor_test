"""Inject mnemonics into learn_seed.json from Learn MD articles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from services.learn_article_md import parse_learn_article_md  # noqa: E402


def main() -> None:
    seed_path = ROOT / "api" / "data" / "learn_seed.json"
    seed: list[dict] = json.loads(seed_path.read_text(encoding="utf-8"))
    by_slug = {item.get("slug"): item for item in seed}

    md_files = {
        "sql-acid-transactions": ROOT
        / "ui/src/data/learn/sql/sql-acid-transactions.md",
        "qa-types-levels": ROOT / "ui/src/data/learn/qa/qa-types-levels.md",
        "sa-http-security-basics": ROOT
        / "ui/src/data/learn/sa/sa-http-security-basics.md",
        "mnemonics-intro": ROOT / "ui/src/data/learn/tools/mnemonics-intro.md",
    }

    updated: list[str] = []
    for slug, path in md_files.items():
        text = path.read_text(encoding="utf-8")
        payload, warnings = parse_learn_article_md(text)
        mnemonics = (payload.get("structured") or {}).get("mnemonics") or []
        print(f"{slug}: mnemonics={len(mnemonics)} warnings={warnings[:3]}")
        if slug == "mnemonics-intro":
            existing = by_slug.get(slug)
            if existing is None:
                seed.append(payload)
                by_slug[slug] = payload
            else:
                existing.clear()
                existing.update(payload)
            updated.append(slug)
            continue
        item = by_slug.get(slug)
        if item is None:
            print(f"  skip missing seed: {slug}")
            continue
        structured = item.get("structured")
        if not isinstance(structured, dict):
            structured = {"version": 1}
            item["structured"] = structured
        structured["mnemonics"] = mnemonics
        updated.append(slug)

    seed_path.write_text(
        json.dumps(seed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("updated", updated)
    print("seed count", len(seed))


if __name__ == "__main__":
    main()

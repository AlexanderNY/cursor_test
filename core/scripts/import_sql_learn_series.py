"""Merge Learn SQL series .md articles into learn_seed.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "core" / "services" / "learn_article_md.py"
_SPEC = importlib.util.spec_from_file_location("learn_article_md", HELPER)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
parse_learn_article_md = _mod.parse_learn_article_md

SEED = ROOT / "core" / "data" / "learn_seed.json"
SERIES_DIR = ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn" / "sql"


def main() -> None:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    if not isinstance(seed, list):
        raise SystemExit("learn_seed.json must be a list")
    by_slug = {
        item.get("slug"): index
        for index, item in enumerate(seed)
        if isinstance(item, dict)
    }
    files = sorted(SERIES_DIR.glob("sql-*.md"))
    if not files:
        raise SystemExit(f"no sql-*.md in {SERIES_DIR}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        payload, warnings = parse_learn_article_md(text)
        slug = payload["slug"]
        for warning in warnings:
            print(f"WARN {slug}: {warning}")
        quiz_count = len((payload.get("structured") or {}).get("quiz") or [])
        anki_count = len((payload.get("structured") or {}).get("anki") or [])
        if quiz_count < 3 or anki_count < 3:
            raise SystemExit(
                f"{slug}: need >=3 quiz and anki, got {quiz_count}/{anki_count}"
            )
        if not (payload.get("structured") or {}).get("lab"):
            raise SystemExit(f"{slug}: missing lab")
        if not (payload.get("structured") or {}).get("cheatsheetHtml"):
            raise SystemExit(f"{slug}: missing cheatsheetHtml")
        if not ((payload.get("structured") or {}).get("diagrams") or []):
            raise SystemExit(f"{slug}: missing diagram")
        profiles = set(payload.get("profiles") or [])
        for required in ("developer", "analyst", "tester"):
            if required not in profiles:
                raise SystemExit(
                    f"{slug}: profiles must include {required}, got {sorted(profiles)}"
                )
        if slug in by_slug:
            seed[by_slug[slug]] = payload
            print(f"updated {slug} quiz={quiz_count} anki={anki_count}")
        else:
            seed.append(payload)
            by_slug[slug] = len(seed) - 1
            print(
                f"appended {slug} order={payload.get('order')} "
                f"quiz={quiz_count} anki={anki_count}"
            )
    SEED.write_text(
        json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"seed count={len(seed)} files={len(files)}")


if __name__ == "__main__":
    main()

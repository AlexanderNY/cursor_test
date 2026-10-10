#!/usr/bin/env python3
"""Shared merge of Learn series .md into learn_seed.json (core + site-api)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Prefer site-api parser (mnemonics + current template); fall back to core copy.
HELPER_CANDIDATES = (
    ROOT / "nine-to-eighteen" / "api" / "services" / "learn_article_md.py",
    ROOT / "core" / "services" / "learn_article_md.py",
)
HELPER = next((path for path in HELPER_CANDIDATES if path.is_file()), HELPER_CANDIDATES[-1])
SEED_PATHS = (
    ROOT / "core" / "data" / "learn_seed.json",
    ROOT / "nine-to-eighteen" / "api" / "data" / "learn_seed.json",
)
LEARN_ROOT = ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learn"

_SPEC = importlib.util.spec_from_file_location("learn_article_md", HELPER)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
parse_learn_article_md = _mod.parse_learn_article_md


def series_dir(name: str) -> Path:
    return LEARN_ROOT / name


def import_series(
    *,
    series_dir: Path,
    glob_pattern: str,
    required_profiles: tuple[str, ...] = (),
    min_quiz: int = 5,
    min_anki: int = 6,
) -> None:
    primary = SEED_PATHS[0]
    seed = json.loads(primary.read_text(encoding="utf-8"))
    if not isinstance(seed, list):
        raise SystemExit("learn_seed.json must be a list")
    by_slug = {
        item.get("slug"): index
        for index, item in enumerate(seed)
        if isinstance(item, dict)
    }
    files = sorted(series_dir.glob(glob_pattern))
    if not files:
        raise SystemExit(f"no {glob_pattern} in {series_dir}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        payload, warnings = parse_learn_article_md(text)
        slug = payload["slug"]
        for warning in warnings:
            try:
                print(f"WARN {slug}: {warning}")
            except UnicodeEncodeError:
                print(f"WARN {slug}: {warning.encode('ascii', 'replace').decode('ascii')}")
        structured = payload.get("structured") or {}
        quiz_count = len(structured.get("quiz") or [])
        anki_count = len(structured.get("anki") or [])
        if quiz_count < min_quiz or anki_count < min_anki:
            raise SystemExit(
                f"{slug}: need >={min_quiz} quiz and >={min_anki} anki, "
                f"got {quiz_count}/{anki_count}"
            )
        if not structured.get("lab"):
            raise SystemExit(f"{slug}: missing lab")
        if not structured.get("cheatsheetHtml"):
            raise SystemExit(f"{slug}: missing cheatsheetHtml")
        if not (structured.get("diagrams") or []):
            raise SystemExit(f"{slug}: missing diagram")
        profiles = set(payload.get("profiles") or [])
        for required in required_profiles:
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
    dumped = json.dumps(seed, ensure_ascii=False, indent=2) + "\n"
    for seed_path in SEED_PATHS:
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        seed_path.write_text(dumped, encoding="utf-8")
        print(f"wrote {seed_path.relative_to(ROOT)}")
    print(f"seed count={len(seed)} files={len(files)}")

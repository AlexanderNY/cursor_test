#!/usr/bin/env python3
"""Regenerate learn episodes.ts from learn_seed.json (deploy + nine-to-eighteen)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "core" / "data" / "learn_seed.json"
OUTS = [
    ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn" / "episodes.ts",
    ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learn" / "episodes.ts",
]


def ts_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def emit_post(item: dict) -> str:
    lines = ["  {"]
    for key in (
        "slug",
        "episode",
        "title",
        "shortTitle",
        "rubricId",
    ):
        lines.append(f"    {key}: {ts_string(str(item.get(key) or ''))},")
    lines.append(f"    order: {int(item.get('order') or 0)},")
    for key in ("theory", "lab", "cheatsheet", "diagram"):
        lines.append(f"    {key}: {ts_string(str(item.get(key) or ''))},")
    links = item.get("links") or []
    lines.append("    links: [")
    for link in links:
        if not isinstance(link, dict):
            continue
        lines.append("      {")
        lines.append(f"        label: {ts_string(str(link.get('label') or ''))},")
        lines.append(f"        href: {ts_string(str(link.get('href') or '#'))},")
        lines.append("      },")
    lines.append("    ],")
    structured = item.get("structured")
    if isinstance(structured, dict) and structured.get("version"):
        dumped = json.dumps(structured, ensure_ascii=False)
        lines.append(f"    structured: {dumped},")
    lines.append("  },")
    return "\n".join(lines)


def main() -> None:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    body = "\n".join(emit_post(item) for item in data if isinstance(item, dict))
    content = (
        "import type { LearnEpisode } from './types'\n\n"
        "/** Auto-generated from core/data/learn_seed.json — do not edit by hand. */\n"
        "export const learnEpisodes: LearnEpisode[] = [\n"
        f"{body}\n"
        "]\n"
    )
    for out in OUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"Wrote {len(data)} episodes to {out}")


if __name__ == "__main__":
    main()

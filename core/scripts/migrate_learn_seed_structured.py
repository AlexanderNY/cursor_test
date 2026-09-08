#!/usr/bin/env python3
"""Migrate learn_seed.json to unified StructuredPost + Anki cards.

Usage:
  python core/scripts/migrate_learn_seed_structured.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "learn_seed.json"


def split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    return parts


def extract_summary_lines(cheatsheet: str) -> list[str]:
    lines: list[str] = []
    for raw in (cheatsheet or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("- [ ]") or line.startswith("- [x]") or line.startswith("- [X]"):
            lines.append(re.sub(r"^- \[[ xX]\]\s*", "", line).strip())
            continue
        if line.startswith("- "):
            lines.append(line[2:].strip())
            continue
        if line.startswith("|") and "---" not in line and not re.match(r"^\|\s*-+", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0].lower() not in ("слой", "параметр", ""):
                lines.append(f"{cells[0]} — {cells[1]}")
    # dedupe keep order
    seen: set[str] = set()
    out: list[str] = []
    for item in lines:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out[:12]


def extract_anki(title: str, short_title: str, cheatsheet: str, theory: str) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    summary = extract_summary_lines(cheatsheet)

    # Table rows: term | definition
    for raw in (cheatsheet or "").splitlines():
        line = raw.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        term, definition = cells[0], cells[1]
        if not term or not definition:
            continue
        if term.lower() in ("слой", "параметр", "id", "ключ", "тип"):
            continue
        if len(definition) < 8:
            continue
        cards.append({"front": f"Что такое «{term}»?", "back": definition})

    # Bullet "term — definition" or "term: definition"
    for item in summary:
        if " — " in item:
            left, right = item.split(" — ", 1)
            if len(left) < 60 and len(right) > 10:
                cards.append({"front": left.strip() + "?", "back": right.strip()})
        elif ": " in item and len(item) < 200:
            left, right = item.split(": ", 1)
            if len(left) < 60 and len(right) > 10:
                cards.append({"front": left.strip() + "?", "back": right.strip()})

    # Ensure minimum cards from title/theory
    while len(cards) < 4:
        paras = split_paragraphs(theory)
        intro = paras[0] if paras else title
        cards.append(
            {
                "front": f"О чём выпуск «{short_title or title}»?",
                "back": intro[:400],
            }
        )
        if len(paras) > 1:
            cards.append(
                {
                    "front": f"Ключевая идея: {short_title or title}",
                    "back": paras[1][:400],
                }
            )
        for idx, item in enumerate(summary[:6]):
            cards.append(
                {
                    "front": f"Запомните ({short_title or title}) #{idx + 1}",
                    "back": item,
                }
            )
        cards.append(
            {
                "front": f"Зачем тема «{short_title or title}» на практике?",
                "back": (paras[-1] if paras else title)[:400],
            }
        )
        if len(cards) < 4:
            cards.append(
                {
                    "front": f"Кратко: {title}",
                    "back": (cheatsheet or theory or title)[:400],
                }
            )
            break

    # Deduplicate fronts
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for card in cards:
        front = card["front"].strip()
        back = card["back"].strip()
        if not front or not back or front in seen:
            continue
        seen.add(front)
        unique.append({"front": front[:200], "back": back[:800]})
        if len(unique) >= 8:
            break

    if not unique:
        unique = [
            {
                "front": f"Тема: {short_title or title}",
                "back": (theory or cheatsheet or title)[:400],
            }
        ]
    return unique


def extract_quiz(short_title: str, episode: str, title: str) -> list[dict[str, str]]:
    return [
        {
            "question": f"Какой код у выпуска «{short_title or title}»?",
            "answer": episode or short_title,
            "explain": title,
        }
    ]


def to_structured(item: dict) -> dict:
    theory = str(item.get("theory") or "")
    cheatsheet = str(item.get("cheatsheet") or "")
    diagram = str(item.get("diagram") or "").strip()
    title = str(item.get("title") or "")
    short_title = str(item.get("shortTitle") or "")
    episode = str(item.get("episode") or "")

    paras = split_paragraphs(theory)
    intro = paras[0] if paras else title
    # Pad intro to validation min length
    if len(intro) < 40:
        intro = f"{intro} Тема выпуска: {title}."

    sections: list[dict[str, str]] = []
    if len(paras) > 1:
        body = "\n\n".join(paras[1:])
        sections.append({"heading": "Основная часть", "body": body})
    else:
        sections.append({"heading": "Основная часть", "body": theory or title})

    if cheatsheet.strip():
        sections.append({"heading": "Шпаргалка", "body": cheatsheet.strip()})

    diagrams = []
    if diagram:
        diagrams.append({"caption": "Схема", "mermaid": diagram})

    summary = extract_summary_lines(cheatsheet)
    if not summary:
        summary = [f"Изучите выпуск {episode}: {short_title or title}"]

    anki = extract_anki(title, short_title, cheatsheet, theory)
    quiz = extract_quiz(short_title, episode, title)

    return {
        "version": 1,
        "intro": intro,
        "sections": sections,
        "diagrams": diagrams,
        "quiz": quiz,
        "anki": anki,
        "summary": summary,
    }


def main() -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("learn_seed.json must be a list")

    migrated = 0
    for item in data:
        if not isinstance(item, dict) or not item.get("slug"):
            continue
        structured = to_structured(item)
        item["structured"] = structured
        # Keep legacy fields for dual-read; theory stays as markdown mirror
        migrated += 1
        anki_n = len(structured["anki"])
        print(f"OK {item['slug']}: anki={anki_n}, sections={len(structured['sections'])}")

    SEED_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Migrated {migrated} posts to {SEED_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Russian map aliases, profile/topic tags, and learning-map leaves for every article."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEARN = ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learn"
MAP = ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learning-map" / "interview-prep.md"
SEEDS = (
    ROOT / "core" / "data" / "learn_seed.json",
    ROOT / "nine-to-eighteen" / "api" / "data" / "learn_seed.json",
)

SERIES = (
    ("python", "py*.md", "Python", "python"),
    ("sql", "sql-*.md", "SQL", "sql"),
    ("java", "jv*.md", "Java", "java"),
    ("js", "js*.md", "JavaScript", "javascript"),
    ("qa", "qa*.md", "QA", "qa"),
    ("sa", "sa-*.md", "Системный анализ", "sa"),
    ("redis", "rd*.md", "Redis", "redis"),
    ("product", "pm*.md", "Продукт", "product"),
)

# Profiles already chosen on the built-in map for seed-only episodes.
SEED_PROFILES: dict[str, list[str]] = {
    "s01e01-sloi": ["developer", "analyst", "devops", "tester", "product_owner"],
    "s01e02-karta": ["developer", "analyst", "devops", "product_owner"],
    "b01-karta": ["developer", "analyst"],
    "b03-python": ["developer"],
    "b04-fastapi-health": ["developer", "tester", "devops"],
    "s01e05-fastapi": ["developer", "analyst", "tester"],
    "b07-notes-api": ["developer"],
    "b08-react-list": ["developer"],
    "b09-react-form": ["developer"],
    "s01e10-react": ["developer"],
    "b12-sklejka": ["developer", "devops"],
    "s01e04-sa": ["analyst", "product_owner", "developer"],
    "map-requirements": ["analyst", "product_owner", "tester"],
    "map-product-backlog": ["product_owner", "analyst"],
    "s01e07-postgres": ["developer", "analyst", "devops", "tester"],
    "s01e08-sql": ["developer", "analyst", "tester"],
    "map-normalization": ["analyst", "developer"],
    "map-sql-nosql": ["developer", "analyst", "devops"],
    "map-redis": ["developer", "devops"],
    "s01e03-git": ["developer", "devops", "tester", "analyst"],
    "b06-git-branch": ["developer", "devops"],
    "b02-git": ["developer"],
    "s01e09-regex": ["developer", "tester", "analyst"],
    "s01e06-insomnia": ["tester", "developer", "analyst"],
    "b05-api-check": ["tester", "developer", "devops"],
    "b10-docker": ["devops", "developer"],
    "b11-compose": ["devops", "developer"],
    "map-cicd": ["devops", "developer", "tester"],
    "map-k8s": ["devops", "developer"],
    "map-networking": ["devops", "developer", "tester"],
    "map-auth-jwt": ["developer", "devops", "tester", "analyst"],
    "map-https-access": ["developer", "devops", "tester"],
    "map-qa": ["tester", "analyst", "developer", "product_owner"],
    "map-e2e": ["tester", "developer", "devops"],
    "map-soft-skills": ["developer", "analyst", "devops", "tester", "product_owner"],
}

SEED_TAGS: dict[str, list[str]] = {
    "s01e01-sloi": ["architecture", "слои"],
    "s01e02-karta": ["architecture", "карта"],
    "b01-karta": ["architecture"],
    "b03-python": ["python"],
    "b04-fastapi-health": ["api", "fastapi"],
    "s01e05-fastapi": ["api", "fastapi"],
    "b07-notes-api": ["api"],
    "b08-react-list": ["frontend", "react"],
    "b09-react-form": ["frontend", "react"],
    "s01e10-react": ["frontend", "react"],
    "b12-sklejka": ["architecture"],
    "s01e04-sa": ["sa", "требования"],
    "map-requirements": ["sa", "требования"],
    "map-product-backlog": ["product", "backlog"],
    "s01e07-postgres": ["sql", "postgresql"],
    "s01e08-sql": ["sql"],
    "map-normalization": ["sql", "моделирование"],
    "map-sql-nosql": ["sql", "nosql"],
    "map-redis": ["redis"],
    "s01e03-git": ["git"],
    "b06-git-branch": ["git"],
    "b02-git": ["git"],
    "s01e09-regex": ["regex"],
    "s01e06-insomnia": ["api"],
    "b05-api-check": ["api"],
    "b10-docker": ["docker"],
    "b11-compose": ["docker"],
    "map-cicd": ["ci", "devops"],
    "map-k8s": ["kubernetes"],
    "map-networking": ["http", "сети"],
    "map-auth-jwt": ["security", "jwt"],
    "map-https-access": ["security", "https"],
    "map-qa": ["qa"],
    "map-e2e": ["qa", "e2e"],
    "map-soft-skills": ["soft-skills"],
}


def alias_from_title(title: str) -> str:
    text = re.split(r"\s+[—–]\s+", title.strip(), maxsplit=1)[0].strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= 28:
        return text
    words = text.split()
    out: list[str] = []
    for word in words:
        trial = " ".join([*out, word])
        if len(trial) > 28:
            break
        out.append(word)
    return " ".join(out) or text[:28].rstrip()


def patch_frontmatter(text: str, *, topic: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return text
    block = match.group(1)
    title_m = re.search(r"^title:\s*(.+)$", block, re.M)
    short_m = re.search(r"^shortTitle:\s*(.+)$", block, re.M)
    if title_m and short_m and not re.search(r"[А-Яа-яЁё]", short_m.group(1)):
        alias = alias_from_title(title_m.group(1).strip().strip("'\""))
        block = re.sub(
            r"^shortTitle:\s*.+$",
            f"shortTitle: {alias}",
            block,
            count=1,
            flags=re.M,
        )
    tags_m = re.search(r"^tags:\s*\[(.*)\]\s*$", block, re.M)
    tags: list[str] = []
    if tags_m:
        tags = [part.strip().strip("'\"") for part in tags_m.group(1).split(",") if part.strip()]
    lower = {tag.lower() for tag in tags}
    if topic.lower() not in lower:
        tags.insert(0, topic)
    if "собеседование" not in lower:
        tags.append("собеседование")
    rendered = "[" + ", ".join(tags) + "]"
    if tags_m:
        block = re.sub(r"^tags:\s*\[.*\]\s*$", f"tags: {rendered}", block, count=1, flags=re.M)
    else:
        block += f"\ntags: {rendered}"
    if not re.search(r"^onKnowledgeMap:\s*true\s*$", block, re.M):
        if re.search(r"^onKnowledgeMap:", block, re.M):
            block = re.sub(r"^onKnowledgeMap:.*$", "onKnowledgeMap: true", block, count=1, flags=re.M)
        else:
            block += "\nonKnowledgeMap: true"
    return f"---\n{block}\n---\n" + text[match.end() :]


def patch_markdown() -> int:
    changed = 0
    for folder, pattern, _branch, topic in SERIES:
        for path in sorted((LEARN / folder).glob(pattern)):
            original = path.read_text(encoding="utf-8")
            updated = patch_frontmatter(original, topic=topic)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed += 1
    return changed


def ensure_faq(structured: dict) -> None:
    sections = structured.setdefault("sections", [])
    if any("частые вопросы" in str(item.get("heading") or "").lower() for item in sections if isinstance(item, dict)):
        return
    quiz = [item for item in (structured.get("quiz") or []) if isinstance(item, dict)]
    if not quiz:
        return
    lines = [
        "Короткие ответы на вопросы, которые чаще всего звучат по теме выпуска. Развёрнутая проверка — в тесте ниже."
    ]
    for item in quiz:
        question = str(item.get("question") or "").strip()
        explain = str(item.get("explain") or item.get("answer") or "").strip()
        if question and explain:
            lines.append(f"**{question}** {explain}")
    body = "\n\n".join(lines)
    insert_at = len(sections)
    for index, section in enumerate(sections):
        if isinstance(section, dict) and str(section.get("heading") or "").lower().startswith("шпаргалка"):
            insert_at = index
            break
    sections.insert(insert_at, {"heading": "Частые вопросы с собеседования", "body": body})


def patch_seed(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "")
        title = str(item.get("title") or "")
        short = str(item.get("shortTitle") or "")
        if title and short and not re.search(r"[А-Яа-яЁё]", short):
            item["shortTitle"] = alias_from_title(title)
        if slug in SEED_PROFILES:
            item["profiles"] = SEED_PROFILES[slug]
            tags = list(SEED_TAGS.get(slug) or [])
            if "собеседование" not in tags:
                tags.append("собеседование")
            item["tags"] = tags
            item.setdefault("level", "junior")
        structured = item.get("structured")
        if isinstance(structured, dict) and slug in SEED_PROFILES:
            ensure_faq(structured)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_map(seed_path: Path) -> int:
    text = MAP.read_text(encoding="utf-8")
    linked = set(re.findall(r"learn:([a-z0-9-]+)", text))
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    by_slug = {str(item.get("slug")): item for item in data if isinstance(item, dict)}
    blocks: list[str] = []
    added = 0
    for folder, pattern, branch, _topic in SERIES:
        lines = [f"## {branch}", ""]
        count = 0
        for path in sorted((LEARN / folder).glob(pattern)):
            raw = path.read_text(encoding="utf-8")
            slug_m = re.search(r"^slug:\s*(\S+)\s*$", raw, re.M)
            short_m = re.search(r"^shortTitle:\s*(.+)$", raw, re.M)
            prof_m = re.search(r"^profiles:\s*\[(.*)\]\s*$", raw, re.M)
            if not slug_m:
                continue
            slug = slug_m.group(1).strip()
            if slug in linked:
                continue
            item = by_slug.get(slug) or {}
            alias = (short_m.group(1).strip() if short_m else "") or str(item.get("shortTitle") or slug)
            profiles = []
            if prof_m:
                profiles = [part.strip() for part in prof_m.group(1).split(",") if part.strip()]
            elif isinstance(item.get("profiles"), list):
                profiles = [str(p) for p in item["profiles"]]
            profile_meta = f" profiles:{','.join(profiles)}" if profiles else ""
            lines.append(f"### {alias} {{learn:{slug}{profile_meta}}}")
            count += 1
            added += 1
        if count:
            blocks.append("\n".join(lines))
    if not blocks:
        print("map: nothing to append")
        return 0
    extra = "\n\n".join(blocks) + "\n"
    if not text.endswith("\n"):
        text += "\n"
    MAP.write_text(text.rstrip() + "\n\n" + extra, encoding="utf-8")
    print(f"map appended leaves={added}")
    return added


def main() -> None:
    print(f"markdown patched={patch_markdown()}")
    for seed in SEEDS:
        patch_seed(seed)
        print(f"seed meta {seed.relative_to(ROOT)}")
    append_map(SEEDS[0])


if __name__ == "__main__":
    main()

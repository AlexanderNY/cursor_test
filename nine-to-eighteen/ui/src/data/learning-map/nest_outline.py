"""Вкладывает статьи карты друг в друга по prerequisites выпусков Learn.

Читает interview-prep.md и frontmatter статей, пишет тот же файл.
Повторный запуск устойчив: у каждой статьи один узел, темы без своего slug — дети.
"""

from __future__ import annotations

import re
from pathlib import Path

MAP_PATH = Path(__file__).resolve().parent / "interview-prep.md"
LEARN_DIR = Path(__file__).resolve().parents[2] / "data" / "learn"

LEVEL_ORDER = {
    "intern": 0,
    "junior": 1,
    "middle": 2,
    "senior": 3,
    "lead": 4,
}
LEVEL_TITLE = {
    "intern": "Стажёр",
    "junior": "Junior",
    "middle": "Middle",
    "senior": "Senior",
    "lead": "Lead",
    "": "Прочее",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
BULLET_RE = re.compile(r"^(\s*)-\s+(.+)$")


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower().rstrip(".,:;")


def parse_meta(raw: str) -> tuple[str, str | None, list[str]]:
    text = re.sub(r"\s+", " ", raw.replace("\u00a0", " ")).strip()
    slug: str | None = None
    profiles: list[str] = []
    brace = re.search(r"\{([^}]*)\}\s*$", text)
    if brace:
        meta = brace.group(1)
        text = text[: brace.start()].strip()
        learn = re.search(r"learn\s*:\s*([a-z0-9-]+)", meta, re.I)
        if learn:
            slug = learn.group(1).lower()
        prof = re.search(r"profiles\s*:\s*([a-z0-9_,\s-]+)", meta, re.I)
        if prof:
            profiles = [part.strip().lower() for part in re.split(r"[,|\s]+", prof.group(1)) if part.strip()]
    text = re.sub(r"(^|\s)#([A-Za-zА-Яа-яЁё0-9_+-]+)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, slug, profiles


def load_articles() -> dict[str, dict[str, object]]:
    found: dict[str, dict[str, object]] = {}
    for path in LEARN_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end < 0:
            continue
        block = text[3:end]
        slug_match = re.search(r"^slug:\s*['\"]?([a-z0-9-]+)", block, re.M)
        if not slug_match:
            continue
        slug = slug_match.group(1).lower()
        short = re.search(r'^shortTitle:\s*"?([^"\n]+)"?', block, re.M)
        level = re.search(r"^level:\s*([a-z]+)", block, re.M)
        prereq = re.search(r"^prerequisites:\s*\[([^\]]*)\]", block, re.M)
        prof = re.search(r"^profiles:\s*\[([^\]]*)\]", block, re.M)
        prereqs = []
        if prereq:
            prereqs = [part.strip().strip("\"'") for part in prereq.group(1).split(",") if part.strip()]
        profiles = []
        if prof:
            profiles = [part.strip().strip("\"'") for part in prof.group(1).split(",") if part.strip()]
        found[slug] = {
            "short": (short.group(1).strip().strip('"') if short else ""),
            "level": (level.group(1).strip() if level else ""),
            "prereqs": prereqs,
            "profiles": profiles,
        }
    return found


class Node:
    def __init__(self, title: str, depth: int) -> None:
        self.title = title
        self.depth = depth
        self.slug: str | None = None
        self.profiles: list[str] = []
        self.children: list[Node] = []


def parse_outline(markdown: str) -> Node:
    root = Node("собеседование", 0)
    stack: list[Node] = [root]
    current_heading = 1
    for raw in markdown.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            continue
        heading = HEADING_RE.match(line)
        if heading:
            depth = len(heading.group(1))
            title, slug, profiles = parse_meta(heading.group(2))
            if depth == 1:
                root.title = title or root.title
                stack[:] = [root]
                current_heading = 1
                continue
            while len(stack) > 1 and stack[-1].depth >= depth:
                stack.pop()
            node = Node(title or "—", depth)
            node.slug = slug
            node.profiles = profiles
            stack[-1].children.append(node)
            stack.append(node)
            current_heading = depth
            continue
        bullet = BULLET_RE.match(line)
        if not bullet:
            continue
        spaces = bullet.group(1).replace("\t", "  ")
        indent = len(spaces) // 2
        depth = current_heading + 1 + indent
        title, slug, profiles = parse_meta(bullet.group(2))
        while len(stack) > 1 and stack[-1].depth >= depth:
            stack.pop()
        node = Node(title or "—", depth)
        node.slug = slug
        node.profiles = profiles
        stack[-1].children.append(node)
        stack.append(node)
    return root


class Article:
    def __init__(self, slug: str, title: str) -> None:
        self.slug = slug
        self.title = title
        self.profiles: list[str] = []
        self.subs: list[tuple[str, list[str]]] = []
        self.children: list[Article] = []
        self.level = ""
        self.prereqs: list[str] = []


def union_profiles(current: list[str], extra: list[str]) -> list[str]:
    seen = set(current)
    for item in extra:
        if item not in seen:
            current.append(item)
            seen.add(item)
    return current


def harvest_branch(branch: Node, catalog: dict[str, dict[str, object]]) -> list[Article]:
    found: list[Article] = []
    by_slug: dict[str, Article] = {}

    def add_sub(article: Article, title: str, profiles: list[str]) -> None:
        if not title or norm(title) == norm(article.title):
            union_profiles(article.profiles, profiles)
            return
        if any(norm(existing) == norm(title) for existing, _profiles in article.subs):
            return
        article.subs.append((title, profiles))

    def unslugged(node: Node) -> list[tuple[str, list[str]]]:
        rows: list[tuple[str, list[str]]] = []
        for child in node.children:
            if child.slug:
                continue
            rows.append((child.title, child.profiles))
            rows.extend(unslugged(child))
        return rows

    def walk(node: Node) -> None:
        if node.slug:
            article = by_slug.get(node.slug)
            meta = catalog.get(node.slug, {})
            short = str(meta.get("short") or "").strip()
            if article is None:
                article = Article(node.slug, node.title)
                article.level = str(meta.get("level") or "")
                article.prereqs = [str(item) for item in meta.get("prereqs") or []]
                article.profiles = list(node.profiles) or list(meta.get("profiles") or [])
                by_slug[node.slug] = article
                found.append(article)
            elif short and norm(node.title) == norm(short) and norm(article.title) != norm(short):
                previous_title = article.title
                previous_profiles = list(article.profiles)
                article.title = node.title
                union_profiles(article.profiles, node.profiles)
                add_sub(article, previous_title, previous_profiles)
            else:
                add_sub(article, node.title, node.profiles)
                union_profiles(article.profiles, node.profiles)
            for title, profiles in unslugged(node):
                add_sub(article, title, profiles)
            for child in node.children:
                if child.slug:
                    walk(child)
            return
        for child in node.children:
            walk(child)

    for child in branch.children:
        walk(child)
    return found


def meta_suffix(slug: str | None, profiles: list[str], prereqs: list[str] | None = None) -> str:
    parts: list[str] = []
    if slug:
        parts.append(f"learn:{slug}")
    if prereqs:
        parts.append("prereq:" + ",".join(prereqs))
    if profiles:
        parts.append("profiles:" + ",".join(profiles))
    if not parts:
        return ""
    return " {" + " ".join(parts) + "}"


def emit_articles(articles: list[Article], lines: list[str]) -> None:
    """Статьи — соседи внутри уровня. Пререквизиты не вкладываются, а рисуются стрелками."""
    named_levels = {article.level for article in articles if article.level}
    grouped = len(articles) > 1 and len(named_levels) > 1

    def emit_one(article: Article, hashes: int) -> None:
        lines.append(
            f"{'#' * hashes} {article.title}{meta_suffix(article.slug, article.profiles, article.prereqs)}"
        )
        for title, profiles in article.subs:
            lines.append(f"- {title}{meta_suffix(None, profiles)}")

    if not grouped:
        for article in articles:
            emit_one(article, 3)
        return

    buckets: dict[str, list[Article]] = {}
    for article in articles:
        buckets.setdefault(article.level or "", []).append(article)
    for level in sorted(buckets, key=lambda item: LEVEL_ORDER.get(item, 9)):
        lines.append(f"### {LEVEL_TITLE.get(level, level or 'Прочее')}")
        for article in buckets[level]:
            emit_one(article, 4)


def rebuild() -> str:
    catalog = load_articles()
    source = MAP_PATH.read_text(encoding="utf-8")
    root = parse_outline(source)
    lines = [
        f"# {root.title}",
        "",
        "Карта подготовки: темы одного выпуска внутри статьи. Стрелка входит в статью из каждого пререквизита.",
        "",
    ]
    deepest = 1
    for branch in root.children:
        lines.append(f"## {branch.title}")
        lines.append("")
        articles = harvest_branch(branch, catalog)
        emit_articles(articles, lines)
        lines.append("")
        deepest = max(deepest, len(articles))
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    MAP_PATH.write_text(text, encoding="utf-8")
    print(f"branches={len(root.children)} deepest_article_chain={deepest} chars={len(text)}")
    return text


if __name__ == "__main__":
    rebuild()

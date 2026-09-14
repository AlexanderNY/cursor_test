"""Parse / serialize Learn articles as Markdown + YAML-like frontmatter."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_RUBRICS = ("architecture", "api", "data", "frontend", "tools")
VALID_PROFILES = ("analyst", "devops", "developer", "tester", "product_owner")
VALID_LEVELS = ("intern", "junior", "middle", "senior", "lead")

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "ui-9to18"
    / "src"
    / "data"
    / "learn"
    / "article-template.md"
)

# Fallback if Docker image has no ui-9to18 tree.
BUNDLE_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "data" / "learn_article_template.md"

FRONTMATTER_RE = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$")
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
MERMAID_RE = re.compile(r"```mermaid\s*([\s\S]*?)```", re.IGNORECASE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _normalize_string_list(
    raw: Any, *, max_item_len: int = 64, max_items: int = 32
) -> list[str]:
    if isinstance(raw, str) and raw.strip():
        items = [part.strip() for part in raw.replace(";", ",").split(",")]
    elif isinstance(raw, list):
        items = [str(item or "").strip() for item in raw]
    else:
        items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = item[:max_item_len]
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
        if len(out) >= max_items:
            break
    return out


def _normalize_profiles(raw: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _normalize_string_list(raw, max_item_len=32, max_items=16):
        value = item.lower()
        if value not in VALID_PROFILES or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _normalize_level(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    return value if value in VALID_LEVELS else ""


def _normalize_prerequisites(raw: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _normalize_string_list(raw, max_item_len=128, max_items=24):
        slug = item.lower().replace(" ", "-")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def _normalize_links(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()[:255]
        href = str(item.get("href") or "").strip()[:1024]
        if label or href:
            out.append({"label": label or href, "href": href or "#"})
    return out


def escape_yaml_scalar(value: str) -> str:
    if re.match(r"^[A-Za-z0-9._/-]+$", value) and value.lower() not in (
        "true",
        "false",
        "null",
    ):
        return value
    return json.dumps(value, ensure_ascii=False)


def parse_yaml_scalar(raw: str) -> str:
    value = raw.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        try:
            return json.loads(value.replace("'", '"') if value.startswith("'") else value)
        except (json.JSONDecodeError, TypeError):
            return value[1:-1]
    return value


def parse_yaml_list(raw: str) -> list[str]:
    text = raw.strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        parts: list[str] = []
        buf = ""
        in_quote = False
        quote_char = ""
        for ch in inner:
            if in_quote:
                buf += ch
                if ch == quote_char:
                    in_quote = False
                continue
            if ch in ('"', "'"):
                in_quote = True
                quote_char = ch
                buf += ch
                continue
            if ch == ",":
                parts.append(parse_yaml_scalar(buf))
                buf = ""
                continue
            buf += ch
        if buf.strip():
            parts.append(parse_yaml_scalar(buf))
        return [p for p in parts if p]
    return [parse_yaml_scalar(p) for p in text.replace(";", ",").split(",") if p.strip()]


def parse_bool(raw: str | None) -> bool | None:
    if raw is None or raw == "":
        return None
    value = raw.strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return None


LEARN_KNOWLEDGE_MAP_TAG = "собеседование"


def has_knowledge_map_tag(tags: list[str]) -> bool:
    needle = LEARN_KNOWLEDGE_MAP_TAG.lower()
    return any(str(tag or "").strip().lower() == needle for tag in tags)


def with_knowledge_map_tag(tags: list[str], enabled: bool) -> list[str]:
    without = [
        tag
        for tag in _normalize_string_list(tags)
        if tag.lower() != LEARN_KNOWLEDGE_MAP_TAG.lower()
    ]
    if not enabled:
        return without
    return [*without, LEARN_KNOWLEDGE_MAP_TAG]


def format_yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(escape_yaml_scalar(v) for v in values) + "]"


def load_article_template() -> str:
    for path in (TEMPLATE_PATH, BUNDLE_TEMPLATE_PATH):
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return (
        "---\n"
        "slug: example\n"
        "title: Пример статьи\n"
        "shortTitle: Пример\n"
        "episode: S01E01\n"
        "rubric: architecture\n"
        "order: 1\n"
        "publishedAt: 2026-01-01T10:00:00+03:00\n"
        "profiles: [developer]\n"
        "level: junior\n"
        "tags: [example]\n"
        "onKnowledgeMap: false\n"
        "durationMin: 20\n"
        "excerpt: Краткий лид статьи.\n"
        "prerequisites: []\n"
        "author: \n"
        "authorUrl: \n"
        "coverUrl: \n"
        "seoTitle: \n"
        "seoDescription: \n"
        "seoKeywords: []\n"
        "canonicalUrl: \n"
        "---\n\n"
        "## Введение\n\n"
        "Кратко опишите тему выпуска и зачем она нужна на собеседовании или в работе.\n\n"
        "## Раздел: Основная часть\n\n"
        "Текст теории…\n\n"
        "## Лаба\n\n"
        "**Цель.** …\n\n"
        "## Схема: Схема\n\n"
        "```mermaid\nflowchart LR\n  A[Тема] --> B[Суть]\n```\n\n"
        "## Тест\n\n"
        "### Вопрос 1?\n\n"
        "**Ответ:** ответ\n\n"
        "**Пояснение:** пояснение\n\n"
        "### Вопрос 2?\n\n"
        "**Ответ:** ответ\n\n"
        "**Пояснение:** пояснение\n\n"
        "### Вопрос 3?\n\n"
        "**Ответ:** ответ\n\n"
        "**Пояснение:** пояснение\n\n"
        "## Шпаргалка\n\n"
        "<h3>Суть</h3>\n<ul><li>…</li></ul>\n\n"
        "## Anki\n\n"
        "### Front: Вопрос?\n\n"
        "Back: ответ\n\n"
        "### Front: Вопрос 2?\n\n"
        "Back: ответ\n\n"
        "### Front: Вопрос 3?\n\n"
        "Back: ответ\n\n"
        "## Итоги\n\n"
        "- Пункт\n\n"
        "## Ссылки\n\n"
        "- [Пример](https://example.com)\n"
    )


def _split_sections(body: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(body))
    if not matches:
        text = body.strip()
        return [("Введение", text)] if text else []
    sections: list[tuple[str, str]] = []
    preamble = body[: matches[0].start()].strip()
    if preamble:
        sections.append(("", preamble))
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append((title, body[start:end].strip()))
    return sections


def _parse_quiz(block: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    chunks = re.split(r"^###\s+", block, flags=re.MULTILINE)
    for chunk in chunks:
        text = chunk.strip()
        if not text:
            continue
        lines = text.splitlines()
        question = lines[0].strip()
        rest = "\n".join(lines[1:]).strip()
        answer = ""
        explain = ""
        answer_match = re.search(
            r"\*\*Ответ:\*\*\s*([^\n]+)", rest, flags=re.IGNORECASE
        )
        explain_match = re.search(
            r"\*\*Пояснение:\*\*\s*([\s\S]*?)(?=\n\*\*|\Z)", rest, flags=re.IGNORECASE
        )
        if answer_match:
            answer = answer_match.group(1).strip()
        if explain_match:
            explain = explain_match.group(1).strip()
        if question or answer:
            items.append(
                {"question": question, "answer": answer, "explain": explain}
            )
    return items


def _parse_anki(block: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    chunks = re.split(r"^###\s+", block, flags=re.MULTILINE)
    for chunk in chunks:
        text = chunk.strip()
        if not text:
            continue
        lines = text.splitlines()
        front_line = lines[0].strip()
        front = re.sub(r"^Front:\s*", "", front_line, flags=re.IGNORECASE).strip()
        rest = "\n".join(lines[1:]).strip()
        back_match = re.search(
            r"^Back:\s*([\s\S]*)$", rest, flags=re.IGNORECASE | re.MULTILINE
        )
        back = back_match.group(1).strip() if back_match else rest
        if front or back:
            items.append({"front": front, "back": back})
    return items


def _parse_links(block: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for line in block.splitlines():
        trimmed = line.strip().lstrip("-* ").strip()
        if not trimmed:
            continue
        match = LINK_RE.search(trimmed)
        if match:
            links.append({"label": match.group(1).strip(), "href": match.group(2).strip()})
            continue
        if "|" in trimmed:
            label, href = trimmed.split("|", 1)
            links.append({"label": label.strip(), "href": href.strip() or "#"})
            continue
        links.append({"label": trimmed, "href": "#"})
    return _normalize_links(links)


def _parse_summary(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        trimmed = line.strip()
        if trimmed.startswith(("-", "*")):
            items.append(trimmed.lstrip("-* ").strip())
        elif trimmed:
            items.append(trimmed)
    return [item for item in items if item]


def parse_learn_article_md(text: str) -> tuple[dict[str, Any], list[str]]:
    """Return (post_payload, warnings). Payload is ready for learn_service.upsert_post."""
    warnings: list[str] = []
    source = text.lstrip("\ufeff")
    match = FRONTMATTER_RE.match(source)
    meta: dict[str, str] = {}
    body = source
    if match:
        for line in match.group(1).splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue
            colon = trimmed.find(":")
            if colon <= 0:
                continue
            key = trimmed[:colon].strip().lower()
            meta[key] = trimmed[colon + 1 :].strip()
        body = match.group(2)
    else:
        warnings.append("Нет YAML frontmatter — метаданные будут пустыми или из fallback")

    def meta_list(key: str) -> list[str]:
        return parse_yaml_list(meta.get(key, "")) if meta.get(key) else []

    rubric = (meta.get("rubric") or meta.get("rubricid") or "architecture").strip().lower()
    if rubric not in VALID_RUBRICS:
        warnings.append(f"Неизвестная рубрика '{rubric}', поставлено architecture")
        rubric = "architecture"

    profiles = _normalize_profiles(meta_list("profiles"))
    for raw in meta_list("profiles"):
        if raw.lower() not in VALID_PROFILES:
            warnings.append(f"Пропущен неизвестный профиль: {raw}")

    level_raw = (meta.get("level") or "").strip().lower()
    level = _normalize_level(level_raw)
    if level_raw and not level:
        warnings.append(f"Неизвестный уровень '{level_raw}'")

    intro = ""
    sections: list[dict[str, str]] = []
    diagrams: list[dict[str, str]] = []
    quiz: list[dict[str, str]] = []
    anki: list[dict[str, str]] = []
    summary: list[str] = []
    lab = ""
    cheatsheet_html = ""
    appendix_parts: list[str] = []
    links: list[dict[str, str]] = []

    for title, content in _split_sections(body):
        lower = title.lower()
        if not title or lower in ("введение", "intro"):
            if not title and content:
                appendix_parts.append(content)
            else:
                intro = (intro + "\n\n" + content).strip() if intro else content
            continue
        if lower.startswith("раздел:") or lower.startswith("section:"):
            heading = title.split(":", 1)[1].strip() if ":" in title else title
            sections.append({"heading": heading, "body": content})
            continue
        if lower in ("лаба", "lab", "лабораторная"):
            lab = content
            continue
        if lower.startswith("схема:") or lower.startswith("diagram:"):
            caption = title.split(":", 1)[1].strip() if ":" in title else title
            mermaid_match = MERMAID_RE.search(content)
            mermaid = mermaid_match.group(1).strip() if mermaid_match else content.strip()
            diagrams.append({"caption": caption, "mermaid": mermaid})
            continue
        if lower in ("тест", "quiz", "тест:"):
            quiz.extend(_parse_quiz(content))
            continue
        if lower in ("шпаргалка", "cheatsheet"):
            cheatsheet_html = content
            continue
        if lower in ("anki", "карточки"):
            anki.extend(_parse_anki(content))
            continue
        if lower in ("итоги", "summary", "выводы"):
            summary.extend(_parse_summary(content))
            continue
        if lower in ("ссылки", "links"):
            links.extend(_parse_links(content))
            continue
        appendix_parts.append(f"## {title}\n\n{content}".strip())
        warnings.append(f"Неизвестный раздел '## {title}' → appendix")

    if not sections and intro:
        # Keep validation friendly: one theory section if only intro present.
        pass

    structured: dict[str, Any] = {
        "version": 1,
        "intro": intro.strip(),
        "sections": sections or [{"heading": "Основная часть", "body": ""}],
        "diagrams": diagrams,
        "quiz": quiz,
        "anki": anki,
        "summary": summary or [""],
    }
    if lab.strip():
        structured["lab"] = lab.strip()
    if cheatsheet_html.strip():
        structured["cheatsheetHtml"] = cheatsheet_html.strip()
    if appendix_parts:
        structured["appendix"] = "\n\n".join(appendix_parts).strip()

    theory_parts = [intro.strip()]
    for section in sections:
        if section.get("heading"):
            theory_parts.append(f"## {section['heading']}")
        if section.get("body"):
            theory_parts.append(section["body"])
    theory = "\n\n".join(part for part in theory_parts if part)
    first_diagram = next(
        (d["mermaid"] for d in diagrams if str(d.get("mermaid") or "").strip()),
        "",
    )

    try:
        order = int(meta.get("order") or 0)
    except ValueError:
        order = 0
        warnings.append("order не число — 0")

    try:
        duration_min = int(meta.get("durationmin") or meta.get("duration_min") or 0)
    except ValueError:
        duration_min = 0
        warnings.append("durationMin не число — 0")

    payload = {
        "slug": (meta.get("slug") or "").strip().lower(),
        "episode": (meta.get("episode") or "").strip(),
        "title": parse_yaml_scalar(meta.get("title") or ""),
        "shortTitle": parse_yaml_scalar(
            meta.get("shorttitle") or meta.get("short_title") or ""
        ),
        "rubricId": rubric,
        "order": order,
        "theory": theory,
        "lab": lab.strip(),
        "cheatsheet": cheatsheet_html.strip(),
        "diagram": first_diagram,
        "links": links,
        "structured": structured,
        "theoryFormat": "markdown",
        "labFormat": "markdown",
        "cheatsheetFormat": "html",
        "profiles": profiles,
        "level": level,
        "tags": _normalize_string_list(meta_list("tags")),
        "excerpt": parse_yaml_scalar(meta.get("excerpt") or ""),
        "durationMin": max(0, duration_min),
        "prerequisites": _normalize_prerequisites(meta_list("prerequisites")),
        "author": parse_yaml_scalar(meta.get("author") or ""),
        "authorUrl": parse_yaml_scalar(
            meta.get("authorurl") or meta.get("author_url") or ""
        ),
        "coverUrl": parse_yaml_scalar(
            meta.get("coverurl") or meta.get("cover_url") or ""
        ),
        "seoTitle": parse_yaml_scalar(
            meta.get("seotitle") or meta.get("seo_title") or ""
        ),
        "seoDescription": parse_yaml_scalar(
            meta.get("seodescription") or meta.get("seo_description") or ""
        ),
        "seoKeywords": _normalize_string_list(
            meta_list("seokeywords") or meta_list("seo_keywords")
        ),
        "canonicalUrl": parse_yaml_scalar(
            meta.get("canonicalurl") or meta.get("canonical_url") or ""
        ),
        "publishedAt": (meta.get("publishedat") or meta.get("published_at") or "").strip(),
    }
    if not payload["slug"]:
        warnings.append("slug пустой")
    if not payload["title"]:
        warnings.append("title пустой")
    payload["profiles"] = _normalize_profiles(payload["profiles"])
    payload["level"] = _normalize_level(payload["level"])
    payload["tags"] = _normalize_string_list(payload["tags"])
    on_map = parse_bool(
        meta.get("onknowledgemap")
        or meta.get("on_knowledge_map")
        or meta.get("on-knowledge-map")
    )
    if on_map is not None:
        payload["tags"] = with_knowledge_map_tag(payload["tags"], on_map)
    payload["prerequisites"] = _normalize_prerequisites(payload["prerequisites"])
    payload["seoKeywords"] = _normalize_string_list(payload["seoKeywords"])
    if not payload["publishedAt"]:
        payload["publishedAt"] = datetime.now(timezone.utc).isoformat()
    return payload, warnings


def serialize_learn_article_md(post: dict[str, Any]) -> str:
    structured = post.get("structured") or {}
    if isinstance(structured, str):
        try:
            structured = json.loads(structured)
        except (json.JSONDecodeError, TypeError):
            structured = {}
    if not isinstance(structured, dict):
        structured = {}

    profiles = _normalize_profiles(post.get("profiles"))
    level = _normalize_level(post.get("level"))
    tags = _normalize_string_list(post.get("tags"))
    prerequisites = _normalize_prerequisites(post.get("prerequisites"))
    seo_keywords = _normalize_string_list(
        post.get("seoKeywords") or post.get("seo_keywords")
    )

    front = [
        "---",
        f"slug: {escape_yaml_scalar(str(post.get('slug') or '').strip())}",
        f"title: {escape_yaml_scalar(str(post.get('title') or '').strip())}",
        f"shortTitle: {escape_yaml_scalar(str(post.get('shortTitle') or post.get('short_title') or '').strip())}",
        f"episode: {escape_yaml_scalar(str(post.get('episode') or '').strip())}",
        f"rubric: {escape_yaml_scalar(str(post.get('rubricId') or post.get('rubric_id') or 'architecture').strip())}",
        f"order: {int(post.get('order') or post.get('sort_order') or 0)}",
        f"publishedAt: {escape_yaml_scalar(str(post.get('publishedAt') or post.get('published_at') or '').strip())}",
        f"profiles: {format_yaml_list(profiles)}",
        f"level: {escape_yaml_scalar(level)}",
        f"tags: {format_yaml_list(tags)}",
        f"onKnowledgeMap: {'true' if has_knowledge_map_tag(tags) else 'false'}",
        f"durationMin: {int(post.get('durationMin') or post.get('duration_min') or 0)}",
        f"excerpt: {escape_yaml_scalar(str(post.get('excerpt') or '').strip())}",
        f"prerequisites: {format_yaml_list(prerequisites)}",
        f"author: {escape_yaml_scalar(str(post.get('author') or '').strip())}",
        f"authorUrl: {escape_yaml_scalar(str(post.get('authorUrl') or post.get('author_url') or '').strip())}",
        f"coverUrl: {escape_yaml_scalar(str(post.get('coverUrl') or post.get('cover_url') or '').strip())}",
        f"seoTitle: {escape_yaml_scalar(str(post.get('seoTitle') or post.get('seo_title') or '').strip())}",
        f"seoDescription: {escape_yaml_scalar(str(post.get('seoDescription') or post.get('seo_description') or '').strip())}",
        f"seoKeywords: {format_yaml_list(seo_keywords)}",
        f"canonicalUrl: {escape_yaml_scalar(str(post.get('canonicalUrl') or post.get('canonical_url') or '').strip())}",
        "---",
        "",
    ]

    parts: list[str] = []
    intro = str(structured.get("intro") or "").strip()
    if intro:
        parts.append(f"## Введение\n\n{intro}")

    for section in structured.get("sections") or []:
        if not isinstance(section, dict):
            continue
        heading = str(section.get("heading") or "Основная часть").strip() or "Основная часть"
        body = str(section.get("body") or "").strip()
        parts.append(f"## Раздел: {heading}\n\n{body}")

    lab = str(structured.get("lab") or post.get("lab") or "").strip()
    if lab:
        parts.append(f"## Лаба\n\n{lab}")

    for diagram in structured.get("diagrams") or []:
        if not isinstance(diagram, dict):
            continue
        caption = str(diagram.get("caption") or "Схема").strip() or "Схема"
        mermaid = str(diagram.get("mermaid") or "").strip()
        if not mermaid:
            continue
        parts.append(f"## Схема: {caption}\n\n```mermaid\n{mermaid}\n```")

    quiz = structured.get("quiz") or []
    if isinstance(quiz, list) and quiz:
        quiz_blocks = ["## Тест", ""]
        for item in quiz:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question") or "").strip()
            answer = str(item.get("answer") or "").strip()
            explain = str(item.get("explain") or "").strip()
            if not (question or answer):
                continue
            quiz_blocks.append(f"### {question}")
            quiz_blocks.append("")
            quiz_blocks.append(f"**Ответ:** {answer}")
            quiz_blocks.append("")
            if explain:
                quiz_blocks.append(f"**Пояснение:** {explain}")
                quiz_blocks.append("")
        parts.append("\n".join(quiz_blocks).strip())

    cheatsheet = str(
        structured.get("cheatsheetHtml") or post.get("cheatsheet") or ""
    ).strip()
    if cheatsheet:
        parts.append(f"## Шпаргалка\n\n{cheatsheet}")

    anki = structured.get("anki") or []
    if isinstance(anki, list) and anki:
        anki_blocks = ["## Anki", ""]
        for item in anki:
            if not isinstance(item, dict):
                continue
            card_front = str(item.get("front") or "").strip()
            card_back = str(item.get("back") or "").strip()
            if not (card_front or card_back):
                continue
            anki_blocks.append(f"### Front: {card_front}")
            anki_blocks.append("")
            anki_blocks.append(f"Back: {card_back}")
            anki_blocks.append("")
        parts.append("\n".join(anki_blocks).strip())

    summary = structured.get("summary") or []
    if isinstance(summary, list):
        bullets = [str(item).strip() for item in summary if str(item).strip()]
        if bullets:
            parts.append("## Итоги\n\n" + "\n".join(f"- {item}" for item in bullets))

    links = _normalize_links(post.get("links"))
    if links:
        link_lines = ["## Ссылки", ""]
        for link in links:
            label = link.get("label") or link.get("href") or ""
            href = link.get("href") or "#"
            link_lines.append(f"- [{label}]({href})")
        parts.append("\n".join(link_lines))

    appendix = str(structured.get("appendix") or "").strip()
    if appendix:
        parts.append(appendix)

    return "\n".join(front) + "\n\n".join(parts).strip() + "\n"

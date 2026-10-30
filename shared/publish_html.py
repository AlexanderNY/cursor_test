"""Allowlisted HTML for posts published as markup (Telegram HTML, WordPress).

Drops script, iframes, event handlers, and unknown tags. Text of dropped tags
is kept and escaped. Anchors keep only a site path or http(s) href.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser

_ALLOWED = frozenset(
    {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "ins",
        "s",
        "strike",
        "del",
        "a",
        "code",
        "pre",
        "blockquote",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "hr",
        "span",
        "tg-spoiler",
    }
)
_VOID = frozenset({"br", "hr"})


def _safe_href(value: str | None) -> str | None:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed or any(ch.isspace() for ch in trimmed):
        return None
    lowered = trimmed.lower()
    if lowered.startswith(("javascript:", "data:", "vbscript:")):
        return None
    if lowered.startswith("/"):
        if len(trimmed) > 1 and trimmed[1] in {"/", "\\"}:
            return None
        return trimmed
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return trimmed
    return None


def _attr(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    for attr_name, attr_value in attrs:
        if attr_name.lower() == name:
            return attr_value
    return None


class _PublishHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        if name not in _ALLOWED:
            return
        if name in _VOID:
            self._parts.append(f"<{name}>")
            return
        if name == "a":
            href = _safe_href(_attr(attrs, "href"))
            if href:
                self._parts.append(f'<a href="{html.escape(href, quote=True)}">')
            else:
                self._parts.append("<a>")
        elif name == "span":
            classes = (_attr(attrs, "class") or "").split()
            if "tg-spoiler" in classes:
                self._parts.append('<span class="tg-spoiler">')
            else:
                self._parts.append("<span>")
        else:
            self._parts.append(f"<{name}>")
        self._stack.append(name)

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name not in _ALLOWED or name in _VOID:
            return
        if name not in self._stack:
            return
        while self._stack:
            opened = self._stack.pop()
            self._parts.append(f"</{opened}>")
            if opened == name:
                break

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(html.escape(data))

    def handle_comment(self, data: str) -> None:
        return

    def result(self) -> str:
        while self._stack:
            self._parts.append(f"</{self._stack.pop()}>")
        return "".join(self._parts)


def sanitize_publish_html(message: str) -> str:
    """Return message limited to the publish tag allowlist."""
    parser = _PublishHtmlSanitizer()
    parser.feed(message or "")
    parser.close()
    return parser.result()

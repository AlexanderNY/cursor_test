"""Sanitize free-text resume fields (about) before DB / PDF."""
from __future__ import annotations

import re

_TAG_RE = re.compile(r"<[^>]+>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_NL_RE = re.compile(r"\n{3,}")
MAX_ABOUT_LEN = 8000


def sanitize_plain_text(value: str, *, max_length: int = MAX_ABOUT_LEN) -> str:
    """Strip HTML/control chars; keep newlines/tabs; truncate."""
    text = str(value or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TAG_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text

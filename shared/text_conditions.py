"""Text phrase / keyword matching shared by TG and VK bots."""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def evaluate_text_conditions(
    text: str,
    conditions: List[str],
    conditions_mode: str = "any_of",
    *,
    category_filter: Optional[str] = None,
    message_category: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """Match keywords/phrases against plain text.

    modes: any_of (default), all_of, regex
    Empty conditions → (False, []) — caller decides if empty means "match all".
    """
    if category_filter:
        if str(message_category or "").lower() != category_filter.lower():
            return False, []

    cleaned = [c.strip() for c in conditions if isinstance(c, str) and c.strip()]
    if not cleaned:
        return False, []

    raw = text or ""
    text_cf = raw.casefold()
    matched: List[str] = []
    mode = (conditions_mode or "any_of").strip()

    if mode == "regex":
        for pattern in cleaned:
            if _safe_regex(raw, pattern):
                matched.append(pattern)
        return bool(matched), matched

    if mode == "all_of":
        for condition in cleaned:
            if condition.casefold() not in text_cf:
                return False, []
            matched.append(condition)
        return True, matched

    for condition in cleaned:
        if condition.casefold() in text_cf:
            matched.append(condition)
    return bool(matched), matched


def should_save_text(
    text: str,
    save_conditions: List[str],
    conditions_mode: str = "any_of",
) -> bool:
    """True if no conditions (save all) or at least one/all phrases match."""
    cleaned = [c for c in (save_conditions or []) if isinstance(c, str) and c.strip()]
    if not cleaned:
        return True
    matched, _ = evaluate_text_conditions(text, cleaned, conditions_mode or "any_of")
    return matched


def _safe_regex(text: str, pattern: str) -> bool:
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        logger.warning("Invalid regex pattern: %s", pattern[:50])
        return False

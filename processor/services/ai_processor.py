"""Замена заглушек AI-обработки через shared/ai_client."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore


async def process_with_ai(text: str, description: str) -> str:
    if not text:
        return text
    if not ai_client:
        return text
    if not description:
        return text
    try:
        return await ai_client.complete(
            prompt=text,
            system=description,
            max_tokens=2048,
        )
    except Exception as exc:
        logger.warning("AI process_with_ai fallback: %s", exc)
        return text


async def summarize_text(text: str, max_length: int) -> str:
    if not text or len(text) <= max_length:
        return text
    if not ai_client:
        return text[:max_length]
    try:
        return await ai_client.summarize(text, max_length)
    except Exception as exc:
        logger.warning("AI summarize fallback: %s", exc)
        return text[:max_length]

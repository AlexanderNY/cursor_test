"""Подготовка текста поста для каждой целевой платформы.

Единая адаптация через shared.post_adapt (лимиты + формат).
Ключи platform_texts — длинные имена (telegram, vkontakte, …).
"""

import logging
from typing import Dict, Optional

from config import PLATFORM_FLAGS
from shared.post_adapt import prepare_platform_texts as _shared_prepare_platform_texts

logger = logging.getLogger(__name__)

# flag to_* → short/long network name accepted by shared.normalize_network
_FLAG_TO_NETWORK = {flag: name for flag, name in PLATFORM_FLAGS.items()}


async def format_for_platform(text: str, max_length: int) -> str:
    """Fit text to max_length (summarize when possible, else truncate)."""
    from shared.post_adapt import fit_text

    return await fit_text(text, "wp", prefer_summarize=True, max_length=max_length)


async def prepare_platform_texts(
    text: str,
    post_flags: Dict[str, bool],
    is_add_static_html: bool = False,
    static_html_content: Optional[str] = None,
) -> Dict[str, str]:
    """Подготавливает тексты для каждой целевой платформы (long keys)."""
    platform_texts = await _shared_prepare_platform_texts(
        text,
        post_flags,
        flag_to_network=_FLAG_TO_NETWORK,
        is_add_static_html=is_add_static_html,
        static_html_content=static_html_content,
        prefer_summarize=True,
        keep_html_for=("tg",),
    )
    for key, value in platform_texts.items():
        logger.debug(
            "Prepared text for %s: %d chars",
            key,
            len(value or ""),
        )
    return platform_texts

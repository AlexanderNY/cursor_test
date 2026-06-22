"""Подготовка текста поста для каждой целевой платформы.

Анализирует флаги to_tg, to_tw, to_wp, to_vk и формирует
тексты, ограниченные лимитами каждой платформы.
"""

import logging
from typing import Dict, Optional

from config import settings, PLATFORM_FLAGS
from services.ai_processor import summarize_text

logger = logging.getLogger(__name__)


def _get_platform_max_length(platform: str) -> int:
    """Возвращает максимальную длину текста для платформы.

    Args:
        platform: Название платформы (wordpress, telegram, twitter, vkontakte).

    Returns:
        Максимальная длина в символах.
    """
    limits = {
        "wordpress": settings.WORDPRESS_MAX_LENGTH,
        "telegram": settings.TELEGRAM_MAX_LENGTH,
        "twitter": settings.TWITTER_MAX_LENGTH,
        "vkontakte": settings.VKONTAKTE_MAX_LENGTH,
        "threads": getattr(settings, "THREADS_MAX_LENGTH", 500),
        "dzen": getattr(settings, "DZEN_MAX_LENGTH", 1500),
        "instagram": getattr(settings, "INSTAGRAM_MAX_LENGTH", 2200),
    }
    return limits.get(platform, settings.WORDPRESS_MAX_LENGTH)


async def format_for_platform(text: str, max_length: int) -> str:
    """Форматирует текст для конкретной платформы с учётом лимита длины.

    На данном этапе — простая обрезка. В будущем будет заменена на
    вызов AI-суммаризации для интеллектуального сокращения.

    Args:
        text: Обработанный текст поста.
        max_length: Максимальная длина для платформы.

    Returns:
        Текст, ограниченный max_length символами.
    """
    if not text or len(text) <= max_length:
        return text

    # TODO: в будущем использовать AI-суммаризацию вместо простой обрезки
    return await summarize_text(text, max_length)


def _append_static_html(text: str, static_html: str, max_length: int) -> str:
    """Добавляет статичный HTML к тексту, если есть место.

    Args:
        text: Текст поста.
        static_html: Статичный HTML для добавления.
        max_length: Максимальная длина текста для платформы.

    Returns:
        Текст с добавленным HTML (если поместился) или исходный текст.
    """
    if not static_html:
        return text

    combined = text + "\n" + static_html
    if len(combined) <= max_length:
        return combined

    logger.debug(
        "Static HTML does not fit: text=%d + html=%d > limit=%d",
        len(text),
        len(static_html),
        max_length,
    )
    return text


async def prepare_platform_texts(
    text: str,
    post_flags: Dict[str, bool],
    is_add_static_html: bool = False,
    static_html_content: Optional[str] = None,
) -> Dict[str, str]:
    """Подготавливает тексты для каждой целевой платформы.

    Анализирует флаги to_tg, to_tw, to_wp, to_vk и для каждой
    активной платформы:
    1. Обрезает текст до лимита платформы
    2. Добавляет статичный HTML (если включено и есть место)

    Args:
        text: Обработанный текст поста.
        post_flags: Словарь флагов {to_tg: bool, to_tw: bool, ...}.
        is_add_static_html: Флаг добавления статичного HTML.
        static_html_content: Содержимое статичного HTML.

    Returns:
        Словарь {platform_name: formatted_text}.
    """
    platform_texts: Dict[str, str] = {}

    for flag_name, platform_name in PLATFORM_FLAGS.items():
        is_active = post_flags.get(flag_name, False)
        if not is_active:
            continue

        max_length = _get_platform_max_length(platform_name)

        # Форматировать (обрезать / суммаризовать) под лимит платформы
        formatted = await format_for_platform(text, max_length)

        # Добавить статичный HTML, если включено и есть место
        if is_add_static_html and static_html_content:
            formatted = _append_static_html(formatted, static_html_content, max_length)

        platform_texts[platform_name] = formatted
        logger.debug(
            "Prepared text for %s: %d chars (limit: %d)",
            platform_name,
            len(formatted),
            max_length,
        )

    return platform_texts

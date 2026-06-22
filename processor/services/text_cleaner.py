"""Модуль очистки текста: удаление эмодзи, картинок, HTML-тегов."""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# ── Список эмодзи для замены / удаления ────────────────────────────
# Формат: (старое значение, новое значение)
# Пустая строка "" — полное удаление.
EMOJI_REPLACEMENTS = [
    ("🔸", "💥"),
    ("Blast", "😤"),
    ("♨️", ""),
    ("💉", ""),
    ("🧩", ""),
    ("⚱️", ""),
    ("📊", ""),
    ("🏦", ""),
    ("🌆", ""),
    ("🔘", ""),
    ("🌏", ""),
    ("🔴", "💥"),
    ("🟢", "💥"),
    ("🕵️‍♀️", ""),
    ("🪨", ""),
    ("🛒", ""),
    ("😔", ""),
    ("💪♀️", ""),
    ("📉", "💥"),
    ("📈", "💥"),
    ("📰", ""),
    ("💻", ""),
    ("📜", "💥"),
    ("⚠️", "💥"),
    ("🛢", ""),
    ("👉", ""),
    ("☕️", ""),
    ("☕", ""),
    ("🔥", ""),
    ("💰", ""),
    ("🚀", ""),
    ("💎", ""),
    ("🎯", ""),
    ("✅", ""),
    ("❌", ""),
    ("⭐", ""),
    ("⭐️", ""),
    ("🏠", ""),
    ("📌", ""),
    ("🔗", ""),
    ("💡", ""),
    ("📢", ""),
    ("🎉", ""),
    ("👇", ""),
    ("👆", ""),
    ("👍", ""),
    ("👎", ""),
    ("🤔", ""),
    ("😱", ""),
    ("😂", ""),
    ("🤣", ""),
    ("❗", ""),
    ("❗️", ""),
    ("❓", ""),
    ("‼️", ""),
    ("⁉️", ""),
    ("✈️", ""),
    ("🛡", ""),
    ("🛡️", ""),
    ("⚡", ""),
    ("⚡️", ""),
    ("🧠", ""),
    ("💬", ""),
    ("📝", ""),
    ("🔐", ""),
    ("🔒", ""),
    ("🔑", ""),
    ("📍", ""),
    ("🏁", ""),
    ("🎁", ""),
    ("🙏", ""),
    ("💸", ""),
    ("🔔", ""),
    ("🔕", ""),
    ("📲", ""),
    ("📱", ""),
    ("🖥", ""),
    ("🖥️", ""),
    ("⬆️", ""),
    ("⬇️", ""),
    ("➡️", ""),
    ("⬅️", ""),
    ("↗️", ""),
    ("↘️", ""),
    ("🔄", ""),
    ("✍️", ""),
    ("📎", ""),
    ("🗓", ""),
    ("🗓️", ""),
    ("⏰", ""),
    ("🕐", ""),
    ("🕑", ""),
    ("🕒", ""),
    ("🕓", ""),
    ("🕔", ""),
    ("🕕", ""),
    ("🕖", ""),
    ("🕗", ""),
    ("🕘", ""),
    ("🕙", ""),
    ("🕚", ""),
    ("🕛", ""),
]

# Regex-паттерн для удаления оставшихся эмодзи (широкий диапазон Unicode)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"             # Zero Width Joiner
    "\U00000023\U0000FE0F\U000020E3"  # Keycap #
    "\U0000002A\U0000FE0F\U000020E3"  # Keycap *
    "\U00002600-\U000026FF"  # Misc Symbols
    "\U00002B05-\U00002B07"  # Arrows
    "\U00002B1B-\U00002B1C"  # Squares
    "\U00002B50"             # Star
    "\U00002B55"             # Circle
    "\U000023E9-\U000023F3"  # Media symbols
    "\U000023F8-\U000023FA"  # Media symbols
    "\U0000203C"             # Double exclamation
    "\U00002049"             # Exclamation question
    "\U000020E3"             # Combining enclosing keycap
    "\U00003030"             # Wavy dash
    "\U000000A9"             # Copyright
    "\U000000AE"             # Registered
    "\U00002122"             # Trademark
    "]+",
    flags=re.UNICODE,
)


def remove_emojis(text: str) -> str:
    """Удаляет эмодзи из текста.

    1. Сначала применяет список конкретных замен (EMOJI_REPLACEMENTS).
    2. Затем убирает оставшиеся эмодзи по Unicode-диапазонам.
    3. Схлопывает множественные пустые строки.

    Args:
        text: Исходный текст.

    Returns:
        Текст без эмодзи.
    """
    if not text:
        return text

    # Шаг 1: конкретные замены
    for old, new in EMOJI_REPLACEMENTS:
        text = text.replace(old, new)

    # Шаг 2: широкая очистка по Unicode-диапазонам
    text = _EMOJI_PATTERN.sub("", text)

    # Шаг 3: схлопнуть множественные пустые строки (3+ → 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_images(text: str, images: List[str]) -> Tuple[str, List[str]]:
    """Удаляет картинки из поста.

    Очищает:
    - HTML-теги <img ...>
    - Markdown-синтаксис ![alt](url)
    - Список вложенных изображений

    Args:
        text: Текст поста.
        images: Список URL изображений.

    Returns:
        Кортеж (очищенный текст, пустой список изображений).
    """
    if not text:
        return text, []

    # Удалить <img> теги (самозакрывающиеся и обычные)
    text = re.sub(r"<img[^>]*\/?>", "", text, flags=re.IGNORECASE)

    # Удалить markdown-картинки: ![alt text](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

    # Удалить теги <picture>...</picture>
    text = re.sub(r"<picture[^>]*>.*?</picture>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Удалить <figure> с картинками
    text = re.sub(r"<figure[^>]*>.*?</figure>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Схлопнуть пустые строки
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip(), []


def clean_html(text: str) -> str:
    """Очищает текст от всех HTML-тегов, оставляя только raw-текст.

    Args:
        text: Текст с HTML-разметкой.

    Returns:
        Текст без HTML-тегов.
    """
    if not text:
        return text

    # Заменить <br>, <br/>, <br /> на перевод строки
    text = re.sub(r"<br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)

    # Заменить закрывающие блочные теги на перевод строки (для сохранения абзацев)
    text = re.sub(r"</(?:p|div|h[1-6]|li|tr|blockquote|section|article)>", "\n", text, flags=re.IGNORECASE)

    # Удалить все оставшиеся HTML-теги
    text = re.sub(r"<[^>]*>", "", text)

    # Декодировать основные HTML-сущности
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")

    # Схлопнуть множественные пустые строки
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Убрать пробелы в конце строк
    text = re.sub(r"[ \t]+\n", "\n", text)

    return text.strip()

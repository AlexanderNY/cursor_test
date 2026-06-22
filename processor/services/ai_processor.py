"""Заглушка для обработки текста нейросетью.

Модуль содержит функции-заглушки, которые в будущем будут заменены
на вызовы API нейронной сети для:
- Обработки текста по описанию (processing_description)
- Суммаризации / сокращения текста с сохранением смысла
"""

import logging

logger = logging.getLogger(__name__)


async def process_with_ai(text: str, description: str) -> str:
    """Обрабатывает текст по описанию с помощью нейросети.

    ЗАГЛУШКА: возвращает текст без изменений.
    В будущем здесь будет вызов API нейросети, которая обработает
    текст в соответствии с инструкцией из processing_description.

    Args:
        text: Исходный текст поста.
        description: Описание обработки (processing_description из профиля).

    Returns:
        Обработанный текст (в текущей реализации — без изменений).
    """
    if not text:
        return text

    if description:
        logger.debug(
            "AI processing stub called with description: '%s' (text length: %d)",
            description[:100],
            len(text),
        )
    else:
        logger.debug("AI processing stub called without description (text length: %d)", len(text))

    # TODO: Заменить на реальный вызов API нейросети
    # Пример будущей реализации:
    # response = await httpx.AsyncClient().post(
    #     AI_API_URL,
    #     json={"text": text, "instruction": description},
    # )
    # return response.json()["result"]

    return text


async def summarize_text(text: str, max_length: int) -> str:
    """Сокращает текст с сохранением смысла (суммаризация).

    ЗАГЛУШКА: обрезает текст до max_length символов.
    В будущем здесь будет вызов API нейросети для интеллектуальной
    суммаризации с сохранением ключевого смысла.

    Args:
        text: Исходный текст.
        max_length: Максимальная длина результата.

    Returns:
        Сокращённый текст.
    """
    if not text or len(text) <= max_length:
        return text

    logger.debug(
        "Summarization stub: truncating text from %d to %d chars",
        len(text),
        max_length,
    )

    # TODO: Заменить на вызов API нейросети для суммаризации
    # Пример будущей реализации:
    # response = await httpx.AsyncClient().post(
    #     AI_API_URL + "/summarize",
    #     json={"text": text, "max_length": max_length},
    # )
    # return response.json()["result"]

    # Временная реализация: простая обрезка
    return text[:max_length]

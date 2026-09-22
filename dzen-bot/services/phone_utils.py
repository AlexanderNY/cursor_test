"""Чистые хелперы для телефона (без Selenium)."""

from __future__ import annotations

import re


class PhoneNormalizeError(ValueError):
    """Некорректный российский номер для ввода на Passport."""


def normalize_ru_phone(raw: str) -> str:
    """
    Нормализует телефон для ввода на passport.yandex.ru: цифры, начинается с 7.
    Примеры: +79001234567 → 79001234567; 89001234567 → 79001234567; 9001234567 → 79001234567.
    """
    digits = re.sub(r"\D", "", (raw or "").strip())
    if not digits:
        raise PhoneNormalizeError("Пустой номер телефона")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    elif digits.startswith("7") and len(digits) == 11:
        pass
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "7" + digits
    elif digits.startswith("7") and len(digits) > 11:
        digits = digits[:11]
    if not (digits.startswith("7") and len(digits) == 11):
        raise PhoneNormalizeError(
            f"Ожидается российский номер в формате 7XXXXXXXXXX (получено {digits!r})."
        )
    return digits

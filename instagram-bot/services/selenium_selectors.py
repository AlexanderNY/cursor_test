"""
Подстроки для поиска элементов Instagram (веб) на главной: RU и EN.

Частичные совпадения снижают риск поломки при смене формулировок.
"""

# Подстроки для поиска подписи к полю логина (логин/телефон/email)
USERNAME_LABEL_SUBSTRINGS: tuple[str, ...] = (
    "Имя пользователя, номер",  # RU
    "Phone number, username",  # EN
    "username, or email",  # EN (хвост фразы)
    "мобильного телефона или",  # RU (часть длинного placeholder)
)

# Подстрока для поля/подписи пароля
PASSWORD_LABEL_SUBSTRINGS: tuple[str, ...] = (
    "Пароль",  # RU — короткое, проверяем с осторожностью (длина)
    "Password",  # EN
)

# aria-label кнопки входа
LOGIN_ARIA_LABELS: tuple[str, ...] = (
    "Вход",
    "Log in",
    "Log In",
)

# Видимый текст кнопки входа (не только button — иногда role=button)
LOGIN_BUTTON_TEXT_SUBSTRINGS: tuple[str, ...] = (
    "Войти",
    "Log in",
    "Log In",
)

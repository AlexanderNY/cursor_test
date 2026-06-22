"""Читаемые сообщения для ошибок Selenium: str(exc) часто даёт только «Message:» без текста."""

from __future__ import annotations


def format_selenium_exception(exc: BaseException) -> str:
    """
    Selenium 4 WebDriverException: пустой msg даёт строку вида «Message:» без пояснения.
    Берём exc.msg, иначе общее описание по типу исключения.
    """
    name = type(exc).__name__
    msg = getattr(exc, "msg", None)
    if isinstance(msg, str):
        m = msg.strip()
        if m:
            return _truncate(f"{name}: {m}")

    raw = (str(exc) or "").strip()
    if raw and not _is_empty_selenium_message(raw):
        return _truncate(f"{name}: {raw}")

    return (
        f"{name}: браузер не вернул текст ошибки. Частые причины: таймаут загрузки страницы Яндекса, "
        "несовместимость версии Chrome/Chromium и chromedriver, сеть или нехватка ресурсов в контейнере. "
        "Полный traceback — в логах dzen-bot."
    )


def _is_empty_selenium_message(raw: str) -> bool:
    r = raw.strip()
    if not r:
        return True
    if r in ("Message:", "Message"):
        return True
    # «Message:\n» или только короткий префикс
    if r.startswith("Message:") and len(r) < 40:
        return True
    return False


def _truncate(s: str, limit: int = 2000) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 3] + "..."

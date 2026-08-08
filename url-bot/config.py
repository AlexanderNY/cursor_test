"""Конфигурация url-bot сервиса из переменных окружения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация url-bot сервиса."""

    # URL core сервиса (для будущего сохранения постов)
    CORE_SERVICE_URL: str = "http://localhost:8002"

    # API Gateway URL
    API_GATEWAY_URL: str = "http://localhost:8000"

    # Таймаут загрузки страницы (секунды)
    PAGE_LOAD_TIMEOUT_SECONDS: int = 30

    # Таймаут ожидания элемента по XPath (секунды)
    ELEMENT_WAIT_TIMEOUT_SECONDS: int = 10

    # Лимит параллельных Chrome-сессий (защита RAM/CPU контейнера)
    SELENIUM_MAX_CONCURRENT: int = 2

    # Сколько ждать свободный слот Selenium; иначе ошибка busy без нового Chrome
    SELENIUM_ACQUIRE_TIMEOUT_SECONDS: float = 60.0

    # Жёсткий потолок одной сессии (Timer → quit/kill); ≥ page load + element wait
    SCRAPE_HARD_TIMEOUT_SECONDS: int = 60

    # Оптимизация скриншота: ресайз и JPEG
    SCREENSHOT_MAX_PIXELS: int = 1920  # макс. сторона (длинная)
    SCREENSHOT_JPEG_QUALITY: int = 85

    # Если задан — сохранять скриншот на диск и возвращать путь вместо base64
    UPLOAD_DIR: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

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

    # Жёсткий потолок одной сессии (Timer → quit/kill); ≥ page load + element wait + screenshot retries
    SCRAPE_HARD_TIMEOUT_SECONDS: int = 90

    # Оптимизация скриншота: ресайз и JPEG
    SCREENSHOT_MAX_PIXELS: int = 1920  # макс. сторона (длинная)
    SCREENSHOT_JPEG_QUALITY: int = 85

    # После появления элемента ждём отрисовки JS/canvas (smart-lab map и т.п.)
    SCREENSHOT_SETTLE_SECONDS: float = 4.0
    # Повторы, если скрин почти однотонный (серый placeholder)
    SCREENSHOT_BLANK_MAX_RETRIES: int = 6
    SCREENSHOT_BLANK_RETRY_SECONDS: float = 2.5
    # Порог «пустого» кадра: мало уникальных цветов на даунсэмпле 32x32
    SCREENSHOT_BLANK_MIN_UNIQUE_COLORS: int = 12

    # Если задан — сохранять скриншот на диск и возвращать путь вместо base64
    UPLOAD_DIR: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

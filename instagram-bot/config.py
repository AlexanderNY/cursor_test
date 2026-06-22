"""Конфигурация Instagram Bot сервиса."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""

    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    UPLOADS_DIR: str = "uploads/instagram"

    LOG_LEVEL: str = "DEBUG"
    LOG_BOT_ACTIONS: bool = True

    API_PORT: int = 8012

    INSTAGRAM_COLLECT_INTERVAL_SEC: int = 300

    PUBLISH_INTERVAL_SEC: int = 60

    RELOAD_PROFILES_INTERVAL_SEC: int = 300

    SESSION_SAVE_PATH: str = ""

    # Одноразовый код 2FA (если в профиле не задан instagram_verification_code), глобальный fallback.
    INSTAGRAM_VERIFICATION_CODE: str = ""

    # HTTP(S) прокси для запросов instagrapi к Instagram (часто нужен при гео/DPI/датацентре).
    # Формат: http://user:pass@host:port или socks5://...
    INSTAGRAM_HTTP_PROXY: str = ""

    # Случайная задержка между запросами instagrapi, секунды [min, max].
    INSTAGRAM_DELAY_RANGE_MIN: int = 1
    INSTAGRAM_DELAY_RANGE_MAX: int = 4

    # Повторы входа при обрыве TLS/сети (SSLError, EOF, timeout и т.п.).
    INSTAGRAM_LOGIN_RETRIES: int = 3
    INSTAGRAM_LOGIN_RETRY_DELAY_SEC: float = 4.0

    # После сбора постов скачивать URL картинок в S3/MinIO (если storage настроен).
    COLLECT_MIRROR_IMAGES_TO_S3: bool = True

    # Selenium fallback (см. services/selenium_driver.py).
    SELENIUM_HEADLESS: bool = True
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 60
    SELENIUM_IMPLICIT_WAIT: int = 5
    CHROME_BIN: str = ""
    CHROMEDRIVER_PATH: str = ""

    # Fallback: вход через браузер (Selenium), если instagrapi не смог авторизоваться.
    INSTAGRAM_SELENIUM_FALLBACK_ENABLED: bool = False
    # Если True — Selenium только при ошибках сети/TLS (ssl, eof, connection, timeout, …).
    # Если False — при любой неудаче instagrapi (может часто запускать Chrome при неверном пароле).
    INSTAGRAM_SELENIUM_FALLBACK_NETWORK_ERRORS_ONLY: bool = True
    # Таймаут ожидания успешного входа в UI (сек).
    SELENIUM_INSTAGRAM_LOGIN_TIMEOUT_SEC: int = 120
    # Макс. размер PNG (КБ) для отдачи base64 в API; больше — только S3.
    SELENIUM_DIAG_MAX_BASE64_KB: int = 512

    # S3-совместимое хранилище (единое с core).
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

"""Конфигурация tw-bot (X / Twitter)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки из переменных окружения."""

    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 2
    DB_POOL_MAXSIZE: int = 8

    LOG_LEVEL: str = "INFO"
    LOG_BOT_ACTIONS: bool = False

    API_PORT: int = 8011

    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""

    CORE_SERVICE_URL: str = "http://localhost:8002"
    URL_BOT_SERVICE_URL: str = "http://localhost:8007"

    PUBLISH_INTERVAL_SEC: int = 60
    FEED_COLLECT_INTERVAL_SEC: int = 300

    DEFAULT_TWEET_SCREENSHOT_XPATH: str = "//article[@data-testid='tweet']"

    # Selenium (verify-x fallback)
    SELENIUM_HEADLESS: bool = True
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 60
    SELENIUM_IMPLICIT_WAIT: int = 5
    CHROME_BIN: str = ""
    CHROMEDRIVER_PATH: str = ""
    SELENIUM_MAX_CONCURRENT: int = 2
    X_SELENIUM_FOLLOWING_MAX_SCROLL: int = 4

    # S3 (диагностические скриншоты Selenium)
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

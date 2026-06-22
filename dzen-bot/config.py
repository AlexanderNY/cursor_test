"""Конфигурация Dzen Bot (Selenium: публикация и сбор ленты)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""

    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    UPLOADS_DIR: str = "uploads"
    CORE_SERVICE_URL: str = "http://localhost:8002"

    LOG_LEVEL: str = "INFO"
    LOG_BOT_ACTIONS: bool = True

    API_PORT: int = 8012

    PUBLISH_INTERVAL_SEC: int = 90
    COLLECT_INTERVAL_SEC: int = 300
    RELOAD_PROFILES_INTERVAL_SEC: int = 0

    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False
    # Префикс ключей для диагностических скриншотов Selenium (имя файла содержит «diag»)
    S3_DIAG_PREFIX: str = "dzen/diag"

    # Selenium
    CHROME_BIN: str = ""
    CHROMEDRIVER_PATH: str = ""
    SELENIUM_HEADLESS: bool = True
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 60
    SELENIUM_IMPLICIT_WAIT: int = 5

    # URL и селекторы (Дзен меняет вёрстку — править через env)
    YANDEX_PASSPORT_URL: str = "https://passport.yandex.ru/auth/"
    # Вход через dzen.ru (см. yandex_dzen_flow) вместо прямого passport
    USE_DZEN_ENTRY_AUTH: bool = True
    DZEN_ENTRY_BASE_URL: str = "https://dzen.ru/"
    PENDING_DZEN_AUTH_TTL_SEC: int = 900
    YANDEX_PASSPORT_LOGIN_TIMEOUT_SEC: int = 50
    YANDEX_PASSPORT_PASSWORD_TIMEOUT_SEC: int = 40
    DZEN_NEW_ARTICLE_URL: str = "https://dzen.ru/article/new?type=article"
    DZEN_SUBSCRIPTIONS_URL: str = "https://dzen.ru/subscriptions"
    DZEN_SUBSCRIPTIONS_WAIT_SEC: int = 45
    DZEN_SUBSCRIPTIONS_SCROLL_TIMES: int = 4
    DZEN_SUBSCRIPTIONS_SCROLL_PAUSE_SEC: float = 1.2
    # Селекторы ссылок на каналы (через запятую); пустые — fallback на все a[href*='dzen.ru']
    DZEN_SUBSCRIPTIONS_LINK_SELECTORS: str = (
        "a[href*='/id/'], a[href*='dzen.ru/id/'], "
        "a[href*='/media/id/'], [data-testid='channel-link'] a"
    )

    # Публикация: поле текста, загрузка картинок, публикация
    DZEN_BODY_SELECTOR: str = "div[data-placeholder], article [contenteditable='true'], .zen-editor [contenteditable='true']"
    DZEN_TITLE_SELECTOR: str = "input[placeholder*='Заголов'], textarea[placeholder*='Заголов'], [data-field='title']"
    DZEN_FILE_INPUT_SELECTOR: str = "input[type='file']"
    DZEN_PUBLISH_BUTTON_XPATH: str = "//button[contains(., 'Опубликовать') or contains(., 'опубликовать')]"

    # Сбор ленты: карточки статей в студии
    DZEN_FEED_ITEM_LINK_SELECTOR: str = "a[href*='/article/'], a[href*='/media/']"
    DZEN_FEED_SCROLL_PAUSE_SEC: float = 1.5
    DZEN_FEED_MAX_SCROLLS: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

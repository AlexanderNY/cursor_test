"""Pydantic модели для Core сервиса."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ==================== Общие типы ====================

class ScheduleType(str, Enum):
    IMMEDIATE = "immediate"
    INTERVALS = "intervals"


class TimeInterval(BaseModel):
    """Временной интервал в формате HH:MM."""
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")


# ==================== Healthcheck ====================

class HealthcheckItem(BaseModel):
    """Результат проверки одного сервиса."""
    service_name: str
    status: str  # "ok" или "error"
    error: Optional[str] = None
    server_time: Optional[str] = None


class HealthcheckResponse(BaseModel):
    """Ответ с результатами healthcheck всех сервисов."""
    services: List[HealthcheckItem]


# ==================== Statistics ====================

class StatisticsItem(BaseModel):
    """Статистика по одному сервису/платформе."""
    service_name: str
    collected_posts: int
    processed_posts: int
    published_posts: int


class StatisticsResponse(BaseModel):
    """Ответ со статистикой всех сервисов."""
    services: List[StatisticsItem]


class UserStatisticsItem(BaseModel):
    """Статистика использования для одного пользователя."""
    user_id: int
    username: str
    email: str
    role: str
    total_posts: int
    collected_posts: int
    processed_posts: int
    published_posts: int


class UserStatisticsResponse(BaseModel):
    """Ответ со статистикой использования по пользователям."""
    users: List[UserStatisticsItem]


# ==================== Schedule Snapshots ====================

class ScheduleSnapshot(BaseModel):
    """Снимок расписания из таблицы schedule_snapshots."""
    user_id: int
    platform: str
    publish_enabled: bool
    collect_enabled: bool
    schedule_type: str
    time_intervals: List[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleResponse(BaseModel):
    """Ответ со списком расписаний."""
    schedules: List[ScheduleSnapshot]


# ==================== Telegram ====================

class TelegramAlertRule(BaseModel):
    """Правило алертинга: мониторинг чатов и оповещение в канал."""
    enabled: bool = True
    chats_to_read: List[str] = Field(default_factory=list, max_length=10)
    save_conditions: List[str] = Field(default_factory=list, max_length=10)
    channel_to_post: Optional[str] = None
    alert_text: Optional[str] = Field(None, max_length=1000)

    @field_validator("chats_to_read", "save_conditions", mode="before")
    @classmethod
    def trim_string_lists(cls, value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        result: List[str] = []
        for item in value:
            if isinstance(item, str):
                trimmed = item.strip()
                if trimmed:
                    result.append(trimmed)
            if len(result) >= 10:
                break
        return result


class TelegramProfileBase(BaseModel):
    """Базовая модель профиля Telegram."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: Optional[str] = "immediate"  # "immediate", "on_new_messages", "by_intervals"
    time_intervals: List[TimeInterval] = []
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    telegram_username: Optional[str] = None
    auth_phone_number: Optional[str] = None
    chats_to_read: List[str] = []
    save_conditions: List[str] = []
    channel_to_post: Optional[str] = None
    alert_enabled: bool = False
    alert_rules: List[TelegramAlertRule] = Field(default_factory=list, max_length=10)
    process_enabled: bool = False
    processing_description: Optional[str] = None
    remove_emojis: bool = False
    remove_images: bool = False
    clean_html: bool = False
    process_services: Optional[List[str]] = None  # ["wordpress", "telegram", "twitter", "vkontakte"]
    status_review_after_process: bool = False
    add_static_html: bool = False
    static_html_content: Optional[str] = None  # max 1000

    @field_validator("alert_rules", mode="before")
    @classmethod
    def limit_alert_rules(cls, value: Any) -> List[Any]:
        if not isinstance(value, list):
            return []
        return value[:10]


class TelegramProfileCreate(TelegramProfileBase):
    """Модель для создания/обновления профиля Telegram."""
    pass


class TelegramProfile(TelegramProfileBase):
    """Модель профиля Telegram с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TelegramPost(BaseModel):
    """Модель поста для Telegram (max 4096 символов)."""
    text: str = Field(..., max_length=4096)
    images: Optional[List[str]] = []
    to_tg: bool = True
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False


class TelegramPostListItem(BaseModel):
    """Модель элемента списка постов Telegram."""
    id: int
    post_text: str
    images: Optional[List[str]] = []
    status: str
    created_at: datetime
    updated_at: datetime


class TelegramPostFull(BaseModel):
    """Модель полного поста Telegram."""
    id: int
    user_id: int
    domain: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    post_text: str
    screenshot: Optional[str] = None
    images: Optional[List[str]] = []
    image_over_text: Optional[str] = None
    comments: int = 0
    reposts: int = 0
    likes: int = 0
    views: int = 0
    is_ad: bool = False
    status: str
    post_type: Optional[str] = None
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    created_at: datetime
    updated_at: datetime


# ==================== Threads ====================

class ThreadsProfileBase(BaseModel):
    """Базовая модель профиля Threads (Meta OAuth)."""
    instagram_handle: Optional[str] = None
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: Optional[str] = "immediate"
    time_intervals: List[TimeInterval] = []
    process_enabled: bool = False
    processing_description: Optional[str] = None
    remove_emojis: bool = False
    remove_images: bool = False
    clean_html: bool = False
    process_services: Optional[List[str]] = None
    status_review_after_process: bool = False
    add_static_html: bool = False
    static_html_content: Optional[str] = None


class ThreadsProfileCreate(ThreadsProfileBase):
    """Модель для создания/обновления профиля Threads (без токенов)."""
    pass


class ThreadsProfile(ThreadsProfileBase):
    """Модель профиля Threads с ID (токены не отдаются)."""
    id: int
    user_id: int
    threads_connected: bool = False
    threads_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThreadsPostListItem(BaseModel):
    """Модель элемента списка постов Threads."""
    id: int
    post_text: str
    images: Optional[List[str]] = []
    status: str
    created_at: datetime
    updated_at: datetime


class ThreadsPostFull(BaseModel):
    """Модель полного поста Threads."""
    id: int
    user_id: int
    domain: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    post_text: str
    screenshot: Optional[str] = None
    images: Optional[List[str]] = []
    image_over_text: Optional[str] = None
    comments: int = 0
    reposts: int = 0
    likes: int = 0
    views: int = 0
    is_ad: bool = False
    status: str
    post_type: Optional[str] = None
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_threads: bool = False
    created_at: datetime
    updated_at: datetime


# ==================== Twitter ====================

class TwitterProfileBase(BaseModel):
    """Базовая модель профиля Twitter."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: ScheduleType = ScheduleType.IMMEDIATE
    time_intervals: List[TimeInterval] = []
    use_proxy: bool = False
    proxy_user: Optional[str] = None
    proxy_pass: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    twitter_username: Optional[str] = None
    twitter_password: Optional[str] = None
    take_screenshot_collect: bool = False
    screenshot_xpath: Optional[str] = None


class TwitterProfileCreate(TwitterProfileBase):
    """Модель для создания/обновления профиля Twitter."""
    pass


class TwitterProfile(TwitterProfileBase):
    """Модель профиля Twitter с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TwitterPost(BaseModel):
    """Модель поста для Twitter (max 280 символов)."""
    text: str = Field(..., max_length=280)
    to_tg: bool = False
    to_tw: bool = True
    to_wp: bool = False
    to_vk: bool = False
    to_threads: bool = False
    to_dzen: bool = False
    to_instagram: bool = False


class TwitterFollowingUser(BaseModel):
    """Пользователь X из списка подписок (following)."""
    id: str
    username: Optional[str] = None
    name: Optional[str] = None


class TwitterFollowingResponse(BaseModel):
    """Ответ GET /tw/following."""
    users: List[TwitterFollowingUser] = []
    next_token: Optional[str] = None
    error: Optional[str] = None


# ==================== WordPress ====================

class WordPressProfileBase(BaseModel):
    """Базовая модель профиля WordPress (legacy)."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: ScheduleType = ScheduleType.IMMEDIATE
    time_intervals: List[TimeInterval] = []
    site_url: Optional[str] = None
    username: Optional[str] = None
    app_password: Optional[str] = None


class WordPressProfileCreate(WordPressProfileBase):
    """Модель для создания/обновления профиля WordPress (legacy)."""
    pass


class WordPressProfile(WordPressProfileBase):
    """Модель профиля WordPress с ID (legacy)."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WordPressPublishProfileCreate(BaseModel):
    """Модель для создания/обновления профиля публикации WordPress.
    time_intervals — одно значение времени в формате "HH:MM".
    publish_all_ready — публиковать все посты, готовые к публикации.
    publish_limit — ограничение количества постов (если publish_all_ready=False).
    publish_interval_minutes — интервал в минутах 15–1440 с шагом 15.
    process_before_publish — обрабатывать перед публикацией.
    process_description — описание обработки.
    """
    publish_enabled: bool = False
    schedule_type: Optional[str] = "on_new_messages"
    time_intervals: Optional[str] = None  # "HH:MM"
    site_url: Optional[str] = None
    username: Optional[str] = None
    app_password: Optional[str] = None
    publish_all_ready: bool = True
    publish_limit: Optional[int] = None
    publish_interval_minutes: Optional[int] = None  # 15–1440, шаг 15
    process_before_publish: bool = False
    process_description: Optional[str] = None
    remove_emojis: bool = False
    remove_images: bool = False
    clean_html: bool = False
    process_services: Optional[List[str]] = None  # ["wordpress", "telegram", "twitter", "vkontakte"]
    status_review_after_process: bool = False
    add_static_html: bool = False
    static_html_content: Optional[str] = None  # max 1000


class CollectSiteItem(BaseModel):
    """Один сайт сбора: site_url, schedule_type, time_intervals (HH:MM)."""
    site_url: Optional[str] = None
    schedule_type: Optional[str] = "on_new_messages"
    time_intervals: Optional[str] = None  # "HH:MM"


class WordPressCollectProfileCreate(BaseModel):
    """Модель для создания/обновления профиля сбора (parser) WordPress.
    collect_sites — список объектов с полями site_url, schedule_type, time_intervals (HH:MM).
    collect_all_available — собрать все доступное; иначе ограничение collect_limit (1–25).
    """
    collect_enabled: bool = False
    collect_sites: Optional[List[Dict[str, Any]]] = []  # [{site_url, schedule_type, time_intervals}]
    collect_all_available: bool = True
    collect_limit: Optional[int] = 1  # 1–25, по умолчанию 1


class WordPressPostContent(BaseModel):
    """Вложенный объект post для реального WordPress."""
    title: str
    content: str = Field(..., max_length=150000)
    status: Optional[str] = None  # draft, publish, pending, private
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = None
    slug: Optional[str] = None
    featured_media: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class WordPressPost(BaseModel):
    """Тело запроса POST /wp/post из ui-app."""
    pageID: Optional[str] = None
    tagIdList: Optional[List[int]] = None
    categoriesIdList: Optional[List[int]] = None
    post: WordPressPostContent
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = True
    to_vk: bool = False
    to_threads: bool = False
    to_dzen: bool = False
    to_instagram: bool = False


# ==================== VKontakte ====================

class VKontakteProfileBase(BaseModel):
    """Базовая модель профиля VKontakte."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: ScheduleType = ScheduleType.IMMEDIATE
    time_intervals: List[TimeInterval] = []
    owner_id: Optional[str] = None
    friends_only: bool = False
    from_group: bool = False
    message: Optional[str] = None
    attachments: Optional[str] = None
    signed: bool = False
    mark_as_ads: bool = False
    # Сбор и публикация (vk-bot)
    access_token: Optional[str] = None
    # Пользовательский OAuth (не токен сообщества): для photos.getWallUploadServer при публикации фото на стену группы
    user_access_token: Optional[str] = None
    # Вычисляемые/сервисные поля (OAuth VK)
    vk_connected: bool = False
    vk_user_id: Optional[int] = None
    groups_to_read: List[int] = []  # ID групп для чтения стены, например [-123456] -> 123456
    users_to_read: List[int] = []  # ID пользователей для чтения стены
    group_to_post: Optional[str] = None  # ID или short_name группы для публикации
    post_to_own_wall: bool = False  # публиковать на личную стену пользователя
    # OAuth-приложение VK (из UI «Авторизация»; fallback — env core)
    vk_app_id: Optional[str] = None
    vk_app_secret: Optional[str] = None
    vk_frontend_url: Optional[str] = None
    vk_public_gateway_url: Optional[str] = None


class VKontakteProfileCreate(VKontakteProfileBase):
    """Модель для создания/обновления профиля VKontakte."""
    pass


class VKontakteProfile(VKontakteProfileBase):
    """Модель профиля VKontakte с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VKontaktePost(BaseModel):
    """Модель поста для VKontakte (max 15985 символов)."""
    text: str = Field(..., max_length=15985)
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = True
    to_threads: bool = False
    to_dzen: bool = False
    to_instagram: bool = False
    images: Optional[List[str]] = None


# ==================== Dzen ====================

class DzenProfileBase(BaseModel):
    """Базовая модель профиля Яндекс Дзен."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: Optional[str] = "immediate"
    time_intervals: List[TimeInterval] = []
    rss_feed_url: Optional[str] = None
    channel_name: Optional[str] = None
    channels_to_read: List[str] = []  # RSS URL чужих каналов для вычитки
    rss_token: Optional[str] = None  # опционально: защита RSS по ?token=...
    yandex_login: Optional[str] = None
    yandex_password: Optional[str] = None  # при сохранении пусто или "***" — не менять в БД
    dzen_studio_url: Optional[str] = None  # URL студии / списка публикаций для Selenium-сбора
    collect_source: Optional[str] = "rss"  # rss | selenium | both


class DzenProfileCreate(DzenProfileBase):
    """Модель для создания/обновления профиля Дзен."""
    pass


class DzenProfile(DzenProfileBase):
    """Модель профиля Дзен с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_auth_error: Optional[str] = None  # выставляется dzen-bot; только чтение в UI

    class Config:
        from_attributes = True


class DzenPost(BaseModel):
    """Модель поста для Дзен (max 1500 символов)."""
    text: str = Field(..., max_length=1500)
    title: Optional[str] = None
    images: Optional[List[str]] = []
    videos: Optional[List[str]] = []  # URL видео или путей после загрузки
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_dzen: bool = True
    to_threads: bool = False
    to_instagram: bool = False


class DzenPostUpdate(BaseModel):
    """Тело запроса для обновления поста Дзен."""
    text: Optional[str] = Field(None, max_length=1500)
    title: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    status: Optional[str] = None


# ==================== Instagram ====================

class InstagramProfileBase(BaseModel):
    """Базовая модель профиля Instagram."""
    publish_enabled: bool = False
    collect_enabled: bool = False
    schedule_type: Optional[str] = "immediate"
    time_intervals: List[TimeInterval] = []
    username: Optional[str] = None
    password: Optional[str] = None
    usernames_to_read: List[str] = []
    process_enabled: bool = False
    processing_description: Optional[str] = None
    remove_emojis: bool = False
    remove_images: bool = False
    clean_html: bool = False
    process_services: Optional[List[str]] = None
    status_review_after_process: bool = False
    add_static_html: bool = False
    static_html_content: Optional[str] = None
    instagram_verification_code: Optional[str] = None


class InstagramProfileCreate(InstagramProfileBase):
    """Модель для создания/обновления профиля Instagram."""
    pass


class InstagramProfile(InstagramProfileBase):
    """Модель профиля Instagram с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    instagram_last_auth_error: Optional[str] = None
    instagram_verification_pending: bool = False
    has_instagram_session: bool = False

    class Config:
        from_attributes = True


class InstagramPost(BaseModel):
    """Модель поста для Instagram (caption max 2200 символов)."""
    caption: str = Field(..., max_length=2200)
    images: Optional[List[str]] = []
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_dzen: bool = False
    to_threads: bool = False
    to_instagram: bool = True


class InstagramPostUpdate(BaseModel):
    """Тело запроса для обновления поста Instagram."""
    caption: Optional[str] = Field(None, max_length=2200)
    images: Optional[List[str]] = None
    status: Optional[str] = None


# ==================== cURL ====================

class CurlTargetSocialNetworks(BaseModel):
    """Целевые соцсети для одного URL."""
    tg: bool = False
    tw: bool = False
    vk: bool = False
    wp: bool = False


class CurlUrlItem(BaseModel):
    """Один URL в настройках cURL: url, xpath, время (HH:MM) и целевые сети."""
    url: str = ""
    xpath: str = ""
    take_screenshot: bool = False
    screenshot_format: Optional[str] = None  # "base64" | "file" — формат скриншота при take_screenshot
    target_social_networks: CurlTargetSocialNetworks = Field(default_factory=CurlTargetSocialNetworks)
    schedule_time: Optional[str] = None  # HH:MM
    run_once: bool = False  # выполнить один раз в заданное время, иначе ежедневно


class CurlSettingsBase(BaseModel):
    """Базовая модель настроек cURL скрапинга (urls + обработка)."""
    collect_enabled: bool = False
    urls: List[CurlUrlItem] = []
    process_before_publish: bool = False
    process_description: Optional[str] = None
    remove_emojis: bool = False
    remove_images: bool = False
    clean_html: bool = False
    process_services: Optional[List[str]] = None
    status_review_after_process: bool = False
    add_static_html: bool = False
    static_html_content: Optional[str] = Field(None, max_length=1000)
    screenshot_only: bool = False


class CurlSettingsCreate(CurlSettingsBase):
    """Модель для создания/обновления настроек cURL."""
    pass


class CurlSettings(CurlSettingsBase):
    """Модель настроек cURL с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UrlPostItem(BaseModel):
    """Один пост из url-bot для сохранения в url_posts."""
    user_id: int
    url: str = ""
    post_text: str = ""
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False


class UrlPostsBatchRequest(BaseModel):
    """Пакет постов из url-bot для сохранения в url_posts."""
    posts: List[UrlPostItem] = Field(default_factory=list)


class CurlOneTimeDoneItem(BaseModel):
    """Одна запись о выполнении одноразового URL (для POST /curl/one-time-done)."""
    user_id: int
    url: str = ""
    xpath: str = ""


class CurlOneTimeDoneRequest(BaseModel):
    """Тело запроса POST /curl/one-time-done (вызывается scheduler после успешного run_once)."""
    items: List[CurlOneTimeDoneItem] = Field(default_factory=list)


# ==================== cPost (ручные посты) ====================

class DefaultPlatforms(BaseModel):
    """Платформы по умолчанию для ручных постов."""
    tg: bool = False
    tw: bool = False
    wp: bool = False
    vk: bool = False
    threads: bool = False
    dzen: bool = False
    instagram: bool = False


class CpostProfileBase(BaseModel):
    """Базовая модель профиля ручных постов."""
    default_platforms: DefaultPlatforms = DefaultPlatforms()


class CpostProfileCreate(CpostProfileBase):
    """Модель для создания/обновления профиля ручных постов."""
    pass


class CpostProfile(CpostProfileBase):
    """Модель профиля ручных постов с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CpostPost(BaseModel):
    """Модель ручного поста — все поля таблицы posts (кроме id, user_id, created_at, updated_at)."""
    text: str = Field(..., max_length=150000)
    title: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    screenshot: Optional[str] = None
    images: List[str] = []
    image_over_text: Optional[str] = None
    comments: int = 0
    reposts: int = 0
    likes: int = 0
    views: int = 0
    is_ad: bool = False
    status: str = "collected"
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_threads: bool = False
    to_dzen: bool = False
    to_instagram: bool = False


class CpostPostUpdate(BaseModel):
    """Модель обновления ручного поста (все поля опциональны)."""
    title: Optional[str] = None
    text: Optional[str] = Field(None, max_length=150000)
    domain: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    screenshot: Optional[str] = None
    images: Optional[List[str]] = None
    image_over_text: Optional[str] = None
    comments: Optional[int] = None
    reposts: Optional[int] = None
    likes: Optional[int] = None
    views: Optional[int] = None
    is_ad: Optional[bool] = None
    status: Optional[str] = None
    to_tg: Optional[bool] = None
    to_tw: Optional[bool] = None
    to_wp: Optional[bool] = None
    to_vk: Optional[bool] = None
    to_threads: Optional[bool] = None
    to_dzen: Optional[bool] = None
    to_instagram: Optional[bool] = None


# ==================== Post (общая модель) ====================

class PostBase(BaseModel):
    """Базовая модель поста."""
    domain: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    post_text: str
    screenshot: Optional[str] = None
    images: List[str] = []
    image_over_text: Optional[str] = None
    comments: int = 0
    reposts: int = 0
    likes: int = 0
    views: int = 0
    is_ad: bool = False
    status: str = "collected"
    post_type: Optional[str] = None
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_dzen: bool = False


class PostCreate(PostBase):
    """Модель для создания поста."""
    pass


class Post(PostBase):
    """Модель поста с ID."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Notifications ====================

class NotificationCreate(BaseModel):
    """Модель для создания уведомления."""
    message: str = Field(..., min_length=1)
    user_id: Optional[int] = None
    type: Optional[str] = "general"  # general, tg_auth_code, tg_auth_2fa, tg_auth_error


class Notification(BaseModel):
    """Модель уведомления."""
    id: int
    message: str
    user_id: Optional[int] = None
    type: Optional[str] = "general"
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Ответ со списком уведомлений."""
    notifications: List[Notification]


# ==================== Feedback ====================

class FeedbackCreate(BaseModel):
    """Модель для создания обратной связи."""
    type: Literal["bug_report", "suggestion", "contact_author"]
    text: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None


class Feedback(BaseModel):
    """Модель обратной связи."""
    id: int
    type: str
    text: str
    email: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """Ответ со списком обратной связи."""
    feedback: List[Feedback]


# ==================== Admin (services status, posts tables) ====================

class LoopStatus(BaseModel):
    """Статус фонового цикла (collector/processor)."""
    last_run_at: Optional[datetime] = None
    total_processed: int = 0
    last_cycle_count: int = 0


class CollectorStatusDetail(BaseModel):
    """Детали статуса collector."""
    service: str = "collector"
    version: str = "1.0.0"
    collect_interval_sec: Optional[int] = None
    distribute_interval_sec: Optional[int] = None
    collector: Optional[LoopStatus] = None
    distributor: Optional[LoopStatus] = None
    current_time: Optional[str] = None
    error: Optional[str] = None


class ProcessorStatusDetail(BaseModel):
    """Детали статуса processor."""
    service: str = "processor"
    version: str = "1.0.0"
    process_interval_sec: Optional[int] = None
    processor: Optional[LoopStatus] = None
    current_time: Optional[str] = None
    error: Optional[str] = None


class SchedulerStatusDetail(BaseModel):
    """Детали статуса scheduler."""
    service: str = "scheduler"
    version: str = "1.0.0"
    poll_interval_sec: Optional[int] = None
    last_poll_at: Optional[datetime] = None
    current_time: Optional[str] = None
    error: Optional[str] = None


class ProcessorRunResponse(BaseModel):
    """Ответ принудительного запуска цикла processor/collect/distribute."""
    status: str
    message: str
    count: int
    errors: Optional[List[str]] = None


class ServicesStatusResponse(BaseModel):
    """Ответ агрегированного статуса сервисов."""
    healthchecks: List[HealthcheckItem]
    collector: Optional[CollectorStatusDetail] = None
    processor: Optional[ProcessorStatusDetail] = None
    scheduler: Optional[SchedulerStatusDetail] = None


class PlatformMetric(BaseModel):
    """Метрика по одной платформе (таблица постов)."""
    platform: str
    table: str
    collected_count: int = 0
    created_count: int = 0
    ready_count: int = 0
    processing_count: int = 0
    status_counts: Dict[str, int] = Field(default_factory=dict)


class PostsTablesResponse(BaseModel):
    """Ответ с обзором таблиц постов."""
    platforms: List[PlatformMetric] = []
    posts_table_collector: Optional[Dict[str, int]] = None
    posts_table_processor: Optional[Dict[str, int]] = None
    collector_error: Optional[str] = None
    processor_error: Optional[str] = None


class PostingDiagnosticsResponse(BaseModel):
    """Результат цикла диагностики постинга (Telegram и пайплайн)."""
    tg_posts_by_status: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Сводка tg_posts: status -> count",
    )
    posts_by_status: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Сводка posts: status, source_platform -> count",
    )
    ready_for_telegram: int = Field(
        default=0,
        description="Число постов в tg_posts со статусом ready с заданным channel_to_post",
    )
    profiles_with_channel: int = Field(
        default=0,
        description="Число tg_profiles с заданным channel_to_post",
    )
    hints: List[str] = Field(
        default_factory=list,
        description="Рекомендации по диагностике",
    )
    collected_at: Optional[str] = Field(
        default=None,
        description="Время сбора диагностики (ISO)",
    )


class PostRow(BaseModel):
    """Одна строка таблицы posts (все столбцы)."""
    id: int
    user_id: int
    domain: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    avatar: Optional[str] = None
    post_date: Optional[datetime] = None
    post_text: Optional[str] = None
    screenshot: Optional[str] = None
    images: Optional[List[Any]] = None
    image_over_text: Optional[str] = None
    comments: int = 0
    reposts: int = 0
    likes: int = 0
    views: int = 0
    is_ad: bool = False
    status: Optional[str] = None
    post_type: Optional[str] = None
    to_tg: bool = False
    to_tw: bool = False
    to_wp: bool = False
    to_vk: bool = False
    to_dzen: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_platform: Optional[str] = None
    source_id: Optional[int] = None

    class Config:
        from_attributes = True


class PostsListResponse(BaseModel):
    """Ответ со списком постов (админ)."""
    posts: List[PostRow] = []


class StorageFileItem(BaseModel):
    """Один объект в S3 (админ: список файлов хранилища)."""
    key: str
    size: int
    last_modified: Optional[str] = None


class StorageFilesResponse(BaseModel):
    """Список файлов в едином хранилище (S3). enabled=False если S3 не настроен."""
    enabled: bool = False
    objects: List[StorageFileItem] = Field(default_factory=list, alias="objects")
    next_continuation_token: Optional[str] = None
    filter_applied: Optional[str] = None
    """Подстрока фильтра по ключу (например diag для скринов Selenium)."""
    pages_scanned: Optional[int] = None
    """Сколько страниц list_objects_v2 просмотрено (только при фильтре по ключу)."""
    filter_truncated: bool = False
    """True если в бакете могли остаться ещё объекты, подходящие под фильтр (лимит страниц/размера выборки)."""


class StoragePresignedUrlResponse(BaseModel):
    """Временная ссылка на скачивание/просмотр объекта в S3."""
    url: str
    expires_in: int = 3600


class StorageDeleteResponse(BaseModel):
    """Результат удаления объекта в S3 (админ)."""
    ok: bool = True
    key: str


class RuntimeGeoByIp(BaseModel):
    """Геоданные по публичному IP (ориентир, не настройка контейнера)."""
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None


class RuntimeLocationResponse(BaseModel):
    """Среда выполнения core: hostname, локальный TZ, публичный IP и гео по IP."""
    hostname: str
    tz_environment_variable: Optional[str] = None
    local_timezone: str
    local_utc_offset: str
    local_now_iso: str
    public_ip: Optional[str] = None
    public_lookup_error: Optional[str] = None
    geo_by_ip: Optional[RuntimeGeoByIp] = None
    geo_lookup_error: Optional[str] = None
    cloud_aws_region: Optional[str] = None

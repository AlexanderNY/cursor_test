"""Проксирование запросов к ботам (schedule и др.)."""

from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(tags=["Bot Proxy"])


async def _forward_to_bot(
    service_url: str,
    path: str,
    request: Request,
    *,
    timeout_seconds: Optional[float] = None,
) -> Response:
    proxy = get_proxy_service()
    target = proxy.build_target_url(service_url.rstrip("/"), path)
    return await proxy.forward_request(
        target, request.method, request, timeout=timeout_seconds
    )


@router.post("/tg-bot/auth/code")
async def tg_bot_auth_code(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /tg-bot/auth/code -> tg-bot /tg/auth/code. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, "/tg/auth/code", request)


@router.post("/tg-bot/auth/password")
async def tg_bot_auth_password(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /tg-bot/auth/password -> tg-bot /tg/auth/password. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, "/tg/auth/password", request)


@router.get("/tg-bot/auth/status/{user_id}")
async def tg_bot_auth_status(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """GET /tg-bot/auth/status/{user_id} -> tg-bot /tg/auth/status/{user_id}. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, f"/tg/auth/status/{user_id}", request)


@router.get("/tg-bot/channels/{user_id}")
async def tg_bot_channels(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """GET /tg-bot/channels/{user_id} -> tg-bot /tg/channels/{user_id}. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, f"/tg/channels/{user_id}", request)


@router.post("/tg-bot/reload")
async def tg_bot_reload(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /tg-bot/reload -> tg-bot /tg/reload. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, "/tg/reload", request)


@router.post("/tg-bot/schedule")
async def tg_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /tg-bot/schedule -> tg-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.TG_BOT_SERVICE_URL, "/schedule", request)


@router.post("/wp-bot/schedule")
async def wp_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /wp-bot/schedule -> wp-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.WP_BOT_SERVICE_URL, "/schedule", request)


@router.post("/vk-bot/schedule")
async def vk_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /vk-bot/schedule -> vk-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.VK_BOT_SERVICE_URL, "/schedule", request)


@router.post("/url-bot/schedule")
async def url_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /url-bot/schedule -> url-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.URL_BOT_SERVICE_URL, "/schedule", request)


@router.post("/tw-bot/schedule")
async def tw_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /tw-bot/schedule -> tw-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.TW_BOT_SERVICE_URL, "/schedule", request)


@router.post("/dzen-bot/schedule")
async def dzen_bot_schedule(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/schedule -> dzen-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.DZEN_BOT_SERVICE_URL, "/schedule", request)


@router.post("/instagram-bot/schedule")
async def instagram_bot_schedule(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram-bot/schedule -> instagram-bot /schedule. Требует JWT."""
    return await _forward_to_bot(settings.INSTAGRAM_BOT_SERVICE_URL, "/schedule", request)


@router.post("/url-bot/run")
async def url_bot_run(request: Request) -> Response:
    """POST /url-bot/run -> url-bot /run. Тестовый запуск скрапинга по запросу (без JWT)."""
    return await _forward_to_bot(settings.URL_BOT_SERVICE_URL, "/run", request)


# ==================== Dzen Bot ====================

@router.get("/dzen-bot/health")
async def dzen_bot_health(request: Request) -> Response:
    """GET /dzen-bot/health -> dzen-bot /health (без JWT)."""
    return await _forward_to_bot(settings.DZEN_BOT_SERVICE_URL, "/health", request)


@router.post("/dzen-bot/publish-once")
async def dzen_bot_publish_once(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/publish-once -> dzen-bot. Требует JWT."""
    return await _forward_to_bot(settings.DZEN_BOT_SERVICE_URL, "/dzen-bot/publish-once", request)


@router.post("/dzen-bot/collect-once")
async def dzen_bot_collect_once(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/collect-once -> dzen-bot. Требует JWT."""
    return await _forward_to_bot(settings.DZEN_BOT_SERVICE_URL, "/dzen-bot/collect-once", request)


@router.post("/dzen-bot/verify-yandex/start")
async def dzen_bot_verify_yandex_start(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/verify-yandex/start -> dzen-bot: старт Selenium-входа; при need_push сессия ждёт push-code."""
    return await _forward_to_bot(
        settings.DZEN_BOT_SERVICE_URL,
        "/dzen-bot/verify-yandex/start",
        request,
        timeout_seconds=180.0,
    )


@router.post("/dzen-bot/verify-yandex/push-code")
async def dzen_bot_verify_yandex_push_code(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/verify-yandex/push-code -> dzen-bot: ввод кода пуш-уведомления."""
    return await _forward_to_bot(
        settings.DZEN_BOT_SERVICE_URL,
        "/dzen-bot/verify-yandex/push-code",
        request,
        timeout_seconds=300.0,
    )


@router.get("/dzen-bot/verify-yandex/pending-diag")
async def dzen_bot_verify_yandex_pending_diag(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /dzen-bot/verify-yandex/pending-diag -> актуальный скрин pending Selenium-сессии."""
    return await _forward_to_bot(
        settings.DZEN_BOT_SERVICE_URL,
        "/dzen-bot/verify-yandex/pending-diag",
        request,
        timeout_seconds=45.0,
    )


@router.post("/dzen-bot/verify-yandex")
async def dzen_bot_verify_yandex(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen-bot/verify-yandex -> dzen-bot: то же, что /start (обратная совместимость)."""
    return await _forward_to_bot(
        settings.DZEN_BOT_SERVICE_URL,
        "/dzen-bot/verify-yandex",
        request,
        timeout_seconds=180.0,
    )


@router.post("/tw-bot/verify-selenium")
async def tw_bot_verify_selenium(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /tw-bot/verify-selenium -> tw-bot: Selenium-вход и список following. Долгий таймаут."""
    return await _forward_to_bot(
        settings.TW_BOT_SERVICE_URL,
        "/tw/verify-selenium",
        request,
        timeout_seconds=300.0,
    )


@router.post("/vk-bot/verify-selenium")
async def vk_bot_verify_selenium(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /vk-bot/verify-selenium -> vk-bot: резервный Selenium-вход и веб-список сообществ. Долгий таймаут."""
    return await _forward_to_bot(
        settings.VK_BOT_SERVICE_URL,
        "/vk-bot/verify-selenium",
        request,
        timeout_seconds=240.0,
    )


# ==================== Threads Bot ====================

@router.get("/threads-bot/auth/status/{user_id}")
async def threads_bot_auth_status(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """GET /th-bot/auth/status/{user_id} -> th-bot."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/auth/status/{user_id}",
        request,
    )


@router.get("/threads-bot/auth/verify/{user_id}")
async def threads_bot_auth_verify(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """GET /threads-bot/auth/verify/{user_id} -> th-bot (проверка токена у Meta)."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/auth/verify/{user_id}",
        request,
    )


@router.get("/threads-bot/auth/url")
async def threads_bot_auth_url(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """GET /th-bot/auth/url -> th-bot (OAuth URL для редиректа)."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/auth/url",
        request,
    )


@router.post("/threads-bot/reload")
async def threads_bot_reload(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /th-bot/reload -> th-bot."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/reload",
        request,
    )


@router.post("/threads-bot/schedule")
async def threads_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST /threads-bot/schedule -> th-bot /threads/schedule."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/schedule",
        request,
    )


@router.post("/threads-bot/selenium/attempt")
async def threads_bot_selenium_attempt(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    """POST -> th-bot /threads/selenium/attempt (диагностический веб-вход Meta, долгий таймаут)."""
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/selenium/attempt",
        request,
        timeout_seconds=180.0,
    )


@router.get("/threads-bot/selenium/session/last")
async def threads_bot_selenium_session_last(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/selenium/session/last",
        request,
    )


@router.get("/threads-bot/selenium/session/{session_id}")
async def threads_bot_selenium_session_get(
    session_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/selenium/session/{session_id}",
        request,
    )


# Алиасы /th-bot/... (в jwt_validator и лимитах); то же проксирование, что и /threads-bot/...
@router.get("/th-bot/auth/status/{user_id}")
async def th_bot_auth_status(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/auth/status/{user_id}",
        request,
    )


@router.get("/th-bot/auth/verify/{user_id}")
async def th_bot_auth_verify(
    user_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/auth/verify/{user_id}",
        request,
    )


@router.get("/th-bot/auth/url")
async def th_bot_auth_url(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/auth/url",
        request,
    )


@router.post("/th-bot/reload")
async def th_bot_reload(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/reload",
        request,
    )


@router.post("/th-bot/schedule")
async def th_bot_schedule(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/schedule",
        request,
    )


@router.post("/th-bot/selenium/attempt")
async def th_bot_selenium_attempt(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/selenium/attempt",
        request,
        timeout_seconds=180.0,
    )


@router.get("/th-bot/selenium/session/last")
async def th_bot_selenium_session_last(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        "/threads/selenium/session/last",
        request,
    )


@router.get("/th-bot/selenium/session/{session_id}")
async def th_bot_selenium_session_get(
    session_id: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
) -> Response:
    return await _forward_to_bot(
        settings.THREADS_BOT_SERVICE_URL,
        f"/threads/selenium/session/{session_id}",
        request,
    )


# ==================== Instagram Bot ====================

@router.post("/instagram-bot/reload")
async def instagram_bot_reload(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram-bot/reload -> instagram-bot /instagram/reload (один проход сбора)."""
    return await _forward_to_bot(settings.INSTAGRAM_BOT_SERVICE_URL, "/instagram/reload", request)


@router.post("/instagram-bot/verify-code")
async def instagram_bot_verify_code(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram-bot/verify-code -> instagram-bot /instagram/verify-code (2FA)."""
    return await _forward_to_bot(settings.INSTAGRAM_BOT_SERVICE_URL, "/instagram/verify-code", request)


@router.post("/instagram-bot/login-test")
async def instagram_bot_login_test(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram-bot/login-test -> instagram-bot /instagram/login-test (проверка входа).

    Долгий таймаут: instagrapi + опционально Selenium fallback и загрузка подписок.
    """
    return await _forward_to_bot(
        settings.INSTAGRAM_BOT_SERVICE_URL,
        "/instagram/login-test",
        request,
        timeout_seconds=300.0,
    )

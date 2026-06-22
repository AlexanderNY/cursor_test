from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/core", tags=["Core"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на core сервис.
    
    Args:
        target_path: Путь на core сервисе
        request: FastAPI Request объект
    
    Returns:
        Response от core сервиса
    """
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request
    )


@router.get("/statistics")
async def get_statistics(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает статистику из core сервиса.
    
    GET /core/statistics -> GET /statistics на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/statistics", request)


@router.get("/healthcheck")
async def get_healthcheck(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает healthcheck из core сервиса.
    
    GET /core/healthcheck -> GET /healthchecks на core сервисе
    Требует JWT аутентификации.
    Внимание: путь меняется с healthcheck на healthchecks!
    """
    return await forward_to_core("/healthchecks", request)


@router.get("/healthchecks")
async def get_healthchecks(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает healthcheck из core сервиса.
    
    GET /core/healthchecks -> GET /healthchecks на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/healthchecks", request)


@router.get("/admin/services-status")
async def get_admin_services_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает агрегированный статус сервисов из core (healthcheck + collector/processor/scheduler).
    
    GET /core/admin/services-status -> GET /admin/services-status на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/admin/services-status", request)


@router.post("/admin/processor/run")
async def run_processor_cycle(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Принудительный запуск одного цикла обработки на processor через core.
    
    POST /core/admin/processor/run -> POST /admin/processor/run на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/admin/processor/run", request)


@router.post("/admin/collect/run")
async def run_collect_cycle(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Принудительный запуск одного цикла сбора на collector (tg_posts → posts).
    
    POST /core/admin/collect/run -> POST /admin/collect/run на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/admin/collect/run", request)


@router.post("/admin/distribute/run")
async def run_distribute_cycle(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Принудительный запуск одного цикла распределения на collector (posts ready → tg_posts ready).
    
    POST /core/admin/distribute/run -> POST /admin/distribute/run на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/admin/distribute/run", request)


@router.get("/admin/posts-tables")
async def get_admin_posts_tables(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает обзор таблиц постов из core (метрики collector и processor).
    
    GET /core/admin/posts-tables -> GET /admin/posts-tables на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/admin/posts-tables", request)


@router.get("/admin/posts")
async def get_admin_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает список постов из core (вся таблица posts, все столбцы).
    
    GET /core/admin/posts -> GET /admin/posts на core сервисе
    Требует JWT аутентификации. Query: limit, offset.
    """
    return await forward_to_core("/admin/posts", request)


@router.get("/admin/posting-diagnostics")
async def get_posting_diagnostics(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Запускает цикл диагностики постинга (tg_posts/posts по статусам и подсказки).
    
    GET /core/admin/posting-diagnostics -> GET /admin/posting-diagnostics на core сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_core("/admin/posting-diagnostics", request)


@router.get("/admin/runtime-location")
async def get_admin_runtime_location(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """IP, гео по IP и локальный TZ процесса core. Только admin (проверка на core).

    GET /core/admin/runtime-location -> GET /admin/runtime-location на core сервисе.
    """
    return await forward_to_core("/admin/runtime-location", request)


@router.get("/admin/storage/files")
async def get_storage_files(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Список файлов в S3-хранилище. Только admin.
    
    GET /core/admin/storage/files -> GET /admin/storage/files на core сервисе.
    """
    return await forward_to_core("/admin/storage/files", request)


@router.get("/admin/storage/presigned-url")
async def get_storage_presigned_url(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Временная ссылка на объект S3 (просмотр PNG диагностики). Только admin."""
    return await forward_to_core("/admin/storage/presigned-url", request)


@router.delete("/admin/storage/files")
async def delete_storage_file(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Удаление объекта в S3. Только admin.

    DELETE /core/admin/storage/files?key=... -> DELETE /admin/storage/files на core.
    """
    return await forward_to_core("/admin/storage/files", request)


@router.get("/schedules")
async def get_schedules(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает сводку расписаний из core сервиса.
    
    GET /core/schedules -> GET /schedules на core сервисе.
    Требует JWT аутентификации. Используется scheduler.
    """
    return await forward_to_core("/schedules", request)


@router.get("/users-statistics")
async def get_users_statistics(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает статистику использования по пользователям из core сервиса.
    
    GET /core/users-statistics -> GET /users-statistics на core сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_core("/users-statistics", request)


@router.get("/group-statistics")
async def get_group_statistics(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает статистику по пользователям своей группы из core сервиса.
    
    GET /core/group-statistics -> GET /group-statistics на core сервисе
    Требует JWT аутентификации и роли manager или admin.
    """
    return await forward_to_core("/group-statistics", request)


@router.get("/schedule")
async def get_schedule(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает расписание из core сервиса.
    
    GET /core/schedule -> GET /schedule на core сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_core("/schedule", request)


async def forward_to_scheduler(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на scheduler сервис.
    
    Args:
        target_path: Путь на scheduler сервисе
        request: FastAPI Request объект
    
    Returns:
        Response от scheduler сервиса
    """
    proxy_service = get_proxy_service()
    from config import settings
    target_url = proxy_service.build_target_url(settings.SCHEDULER_SERVICE_URL, target_path)
    
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request
    )


@router.post("/start-discovery")
async def start_discovery(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Запускает сбор расписаний на scheduler сервисе.
    
    POST /core/start-discovery -> POST /start-discovery на scheduler сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_scheduler("/start-discovery", request)


@router.post("/start-bot")
async def start_bot(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Запускает боты на scheduler сервисе.
    
    POST /core/start-bot -> POST /start-bot на scheduler сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_scheduler("/start-bot", request)


@router.post("/notifications")
async def create_notification(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Создает уведомление на core сервисе.
    
    POST /core/notifications -> POST /notifications на core сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_core("/notifications", request)


@router.get("/notifications")
async def get_notifications(
    request: Request
) -> Response:
    """Получает уведомления из core сервиса.
    
    GET /core/notifications -> GET /notifications на core сервисе
    Не требует аутентификации - доступно всем пользователям.
    """
    return await forward_to_core("/notifications", request)


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Удаляет уведомление на core сервисе.
    
    DELETE /core/notifications/{id} -> DELETE /notifications/{id} на core сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_core(f"/notifications/{notification_id}", request)


@router.post("/feedback")
async def create_feedback(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Создаёт запись обратной связи на core сервисе.

    POST /core/feedback -> POST /feedback на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/feedback", request)


@router.get("/feedback")
async def get_feedback(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Получает список обратной связи из core сервиса.

    GET /core/feedback -> GET /feedback на core сервисе
    Требует JWT и роли admin (проверка на core).
    """
    return await forward_to_core("/feedback", request)


@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Удаляет запись обратной связи на core сервисе.

    DELETE /core/feedback/{id} -> DELETE /feedback/{id} на core сервисе
    Требует JWT и роли admin (проверка на core).
    """
    return await forward_to_core(f"/feedback/{feedback_id}", request)

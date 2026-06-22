"""Роутер админ-эндпоинтов: статус сервисов и обзор таблиц постов."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies import get_admin_user
from services.admin_service import admin_service
from services.post_service import post_service
from storage_client import get_storage
from schemas import (
    ServicesStatusResponse,
    PostsTablesResponse,
    PostsListResponse,
    PostRow,
    ProcessorRunResponse,
    PostingDiagnosticsResponse,
    StorageFileItem,
    StorageFilesResponse,
    StoragePresignedUrlResponse,
    StorageDeleteResponse,
    RuntimeLocationResponse,
)


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/services-status", response_model=ServicesStatusResponse)
async def get_services_status():
    """Агрегированный статус всех сервисов (healthcheck + collector/processor/scheduler status)."""
    data = await admin_service.get_services_status()
    return data


@router.post("/processor/run", response_model=ProcessorRunResponse)
async def run_processor_cycle():
    """Принудительный запуск одного цикла обработки на processor."""
    data = await admin_service.run_processor_cycle()
    return ProcessorRunResponse(**data)


@router.post("/collect/run", response_model=ProcessorRunResponse)
async def run_collect_cycle():
    """Принудительный запуск одного цикла сбора на collector (tg_posts → posts)."""
    data = await admin_service.run_collect_cycle()
    return ProcessorRunResponse(**data)


@router.post("/distribute/run", response_model=ProcessorRunResponse)
async def run_distribute_cycle():
    """Принудительный запуск одного цикла распределения на collector (posts ready → tg_posts ready)."""
    data = await admin_service.run_distribute_cycle()
    return ProcessorRunResponse(**data)


@router.get("/posts-tables", response_model=PostsTablesResponse)
async def get_posts_tables():
    """Обзор таблиц постов: метрики из collector и processor."""
    data = await admin_service.get_posts_tables_overview()
    return data


@router.get("/posts", response_model=PostsListResponse)
async def get_admin_posts(
    request: Request,
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Фильтр по статусу (например review)"),
):
    """Список постов из таблицы posts (все столбцы). При наличии X-User-Id возвращаются только посты этого автора."""
    user_id: Optional[int] = None
    x_user_id = request.headers.get("X-User-Id")
    if x_user_id is not None:
        try:
            user_id = int(x_user_id)
        except ValueError:
            pass
    rows = await post_service.get_all_posts(limit=limit, offset=offset, status=status, user_id=user_id)
    posts = [PostRow.model_validate(r) for r in rows]
    return PostsListResponse(posts=posts)


@router.get("/posting-diagnostics", response_model=PostingDiagnosticsResponse)
async def get_posting_diagnostics():
    """Цикл диагностики постинга: сводки tg_posts/posts по статусам и подсказки для администратора."""
    data = await admin_service.run_posting_diagnostics()
    return PostingDiagnosticsResponse(**data)


@router.get("/runtime-location", response_model=RuntimeLocationResponse)
async def get_runtime_location(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    """Публичный IP, гео по IP и локальный часовой пояс процесса core (контейнера). Только admin."""
    del admin_user
    data = await admin_service.get_runtime_location()
    return RuntimeLocationResponse(**data)


MAX_S3_PAGES_KEY_FILTER = 50


async def _list_storage_with_key_contains(
    storage: Any,
    *,
    prefix: str,
    limit: int,
    key_contains: str,
) -> tuple[list[dict], Optional[str], int, bool]:
    """Собирает до limit объектов, у которых key содержит key_contains (без учёта регистра)."""
    needle = key_contains.strip().lower()
    if not needle:
        result = await storage.list_objects(prefix=prefix or "", max_keys=limit, continuation_token=None)
        return result["objects"], result.get("next_continuation_token"), 1, False

    matches: list[dict] = []
    token: Optional[str] = None
    pages = 0
    truncated = False
    while len(matches) < limit and pages < MAX_S3_PAGES_KEY_FILTER:
        result = await storage.list_objects(
            prefix=prefix or "",
            max_keys=1000,
            continuation_token=token,
        )
        pages += 1
        for obj in result.get("objects") or []:
            key = obj.get("key") or ""
            if needle in key.lower():
                matches.append(obj)
                if len(matches) >= limit:
                    break
        token = result.get("next_continuation_token")
        if not token:
            break
    if token and (pages >= MAX_S3_PAGES_KEY_FILTER or len(matches) >= limit):
        truncated = True
    # При клиентском фильтре токен продолжения S3 не передаём — список несовместим с постраничкой
    return matches, None, pages, truncated


@router.get("/storage/files", response_model=StorageFilesResponse)
async def get_storage_files(
    prefix: Optional[str] = Query(None, description="Фильтр по префиксу ключа (например vk/, uploads/)"),
    limit: int = Query(500, ge=1, le=2000, description="Максимум объектов в ответе"),
    continuation_token: Optional[str] = Query(None, description="Токен для следующей страницы"),
    key_contains: Optional[str] = Query(
        None,
        description="Подстрока в полном ключе объекта (без учёта регистра). Для скриншотов ошибок Selenium используйте diag",
        max_length=200,
    ),
    admin_user: Dict[str, Any] = Depends(get_admin_user),
):
    """Список файлов в едином S3-хранилище. Только admin. Если S3 не настроен — enabled=False.

    Параметр key_contains позволяет отобрать только объекты, в имени ключа которых есть подстрока
    (например «diag» — диагностические PNG при сбоях Selenium в vk/tw/instagram ботах).
    """
    del admin_user  # ensure admin role (checked by dependency)
    storage = get_storage()
    if not storage:
        return StorageFilesResponse(enabled=False, objects=[])

    kc = (key_contains or "").strip()
    if kc:
        raw_objects, next_tok, pages_scanned, truncated = await _list_storage_with_key_contains(
            storage,
            prefix=prefix or "",
            limit=limit,
            key_contains=kc,
        )
        items = [StorageFileItem(**obj) for obj in raw_objects]
        return StorageFilesResponse(
            enabled=True,
            objects=items,
            next_continuation_token=next_tok,
            filter_applied=kc,
            pages_scanned=pages_scanned,
            filter_truncated=truncated,
        )

    result = await storage.list_objects(
        prefix=prefix or "",
        max_keys=limit,
        continuation_token=continuation_token,
    )
    items = [StorageFileItem(**obj) for obj in result["objects"]]
    return StorageFilesResponse(
        enabled=True,
        objects=items,
        next_continuation_token=result.get("next_continuation_token"),
    )


@router.get("/storage/presigned-url", response_model=StoragePresignedUrlResponse)
async def get_storage_presigned_url(
    key: str = Query(..., min_length=1, description="Ключ объекта в бакете"),
    expires_in: int = Query(3600, ge=60, le=86400, description="Срок жизни ссылки в секундах"),
    admin_user: Dict[str, Any] = Depends(get_admin_user),
):
    """Временная ссылка для просмотра/скачивания файла из S3 (например PNG диагностики). Только admin."""
    del admin_user
    storage_key = _validate_storage_key(key)
    storage = get_storage()
    if not storage:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured",
        )
    url = await storage.get_presigned_url(storage_key, expires_in=expires_in)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not generate presigned URL",
        )
    return StoragePresignedUrlResponse(url=url, expires_in=expires_in)


def _validate_storage_key(key: str) -> str:
    k = (key or "").strip().lstrip("/")
    if not k:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'key' is required and cannot be empty",
        )
    if ".." in k or k.startswith("\\"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage key",
        )
    return k


@router.delete("/storage/files", response_model=StorageDeleteResponse)
async def delete_storage_file(
    key: str = Query(..., min_length=1, description="Ключ объекта в бакете (полный путь, например uploads/tg/x.png)"),
    admin_user: Dict[str, Any] = Depends(get_admin_user),
):
    """Удаляет один объект в S3. Только admin."""
    del admin_user
    storage_key = _validate_storage_key(key)
    storage = get_storage()
    if not storage:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 storage is not configured",
        )
    try:
        await storage.delete_object(storage_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to delete object: {e!s}",
        ) from e
    return StorageDeleteResponse(ok=True, key=storage_key)

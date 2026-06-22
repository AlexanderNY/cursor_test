"""Scheduler: опрос core, сохранение расписаний, оповещение ботов."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from config import settings, SCHEDULER_FUNCTIONS_FOR_ADMIN
from database import init_db, close_db
from services.schedule_poll_service import (
    poll_loop, 
    run_poll_cycle, 
    _notify_bot, 
    _fetch_schedules,
    _fetch_profiles_parallel,
    _transform_profiles_to_schedules,
    _store_snapshot,
    get_last_poll_at,
    BOT_PLATFORMS
)
from schemas import StartBotRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

_task: asyncio.Task | None = None
_started_at: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _task, _started_at
    await init_db()
    _started_at = datetime.utcnow()
    _task = asyncio.create_task(poll_loop())
    logger.info("Scheduler started; poll every %s s", settings.POLL_INTERVAL_SECONDS)
    yield
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    await close_db()
    logger.info("Scheduler stopped")


app = FastAPI(title="Scheduler", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {"service": "scheduler", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scheduler", "server_time": datetime.utcnow().isoformat() + "Z"}


@app.get("/status")
async def status():
    """Статус фонового цикла опроса и конфигурация (для админки)."""
    last = get_last_poll_at()
    return {
        "service": "scheduler",
        "version": "1.0.0",
        "poll_interval_sec": settings.POLL_INTERVAL_SECONDS,
        "notify_on_change_only": settings.NOTIFY_ON_CHANGE_ONLY,
        "last_poll_at": last.isoformat() if last and hasattr(last, "isoformat") else last,
        "current_time": datetime.utcnow().isoformat() + "Z",
        "started_at": _started_at.isoformat() + "Z" if _started_at else None,
        "schedule_functions": SCHEDULER_FUNCTIONS_FOR_ADMIN,
    }


async def get_auth_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Получение токена авторизации из заголовков."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required"
        )
    return credentials.credentials


@app.post("/start-discovery")
async def start_discovery(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Принудительный запуск одного цикла сбора расписаний.
    
    Выполняет один цикл: запрос core, diff, сохранение, оповещение.
    """
    try:
        token = await get_auth_token(credentials)
        changed = await run_poll_cycle(token)
        return {
            "status": "success",
            "message": "Discovery cycle completed",
            "changed": changed
        }
    except Exception as e:
        logger.exception("Start discovery error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start discovery: {str(e)}"
        )


@app.get("/schedules")
async def get_schedules(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Получает расписания из профилей через API Gateway и сохраняет в schedule_snapshots.
    
    Выполняет:
    1. Параллельные запросы профилей через API Gateway (wp, tg, tw, vk, threads, dzen, instagram)
    2. Преобразование профилей в формат расписаний
    3. Сохранение в таблицу schedule_snapshots
    4. Возврат собранных расписаний
    """
    try:
        token = await get_auth_token(credentials)
        
        # Параллельно получаем все профили
        profiles_data = await _fetch_profiles_parallel(token)
        
        # Преобразуем профили в формат расписаний
        schedules = _transform_profiles_to_schedules(profiles_data)
        
        # Сохраняем в schedule_snapshots
        await _store_snapshot(schedules)
        
        return {
            "status": "success",
            "message": "Schedules collected and saved",
            "schedules": schedules,
            "count": len(schedules)
        }
    except Exception as e:
        logger.exception("Get schedules error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {str(e)}"
        )


@app.post("/start-bot")
async def start_bot(
    request: StartBotRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Принудительный запуск ботов для указанных платформ.
    
    Args:
        request: Запрос с списком платформ для запуска
        credentials: JWT токен авторизации
    """
    try:
        token = await get_auth_token(credentials)
        
        # Валидация платформ (совпадает с BOT_PLATFORMS в schedule_poll_service)
        valid_platforms = list(BOT_PLATFORMS)
        invalid_platforms = [p for p in request.platforms if p not in valid_platforms]
        if invalid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platforms: {invalid_platforms}. Valid platforms: {valid_platforms}"
            )
        
        # Получаем расписания для указанных платформ
        schedules = await _fetch_schedules(token)
        by_platform: dict[str, list[dict]] = {p: [] for p in request.platforms}
        
        for s in schedules:
            p = s.get("platform")
            if p in by_platform:
                by_platform[p].append(s)
        
        # Запускаем боты для каждой платформы
        results = {}
        for platform in request.platforms:
            try:
                await _notify_bot(platform, by_platform[platform], token)
                results[platform] = {
                    "status": "success",
                    "schedules_count": len(by_platform[platform])
                }
            except Exception as e:
                logger.exception("Failed to start bot %s: %s", platform, e)
                results[platform] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "message": "Bots started",
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Start bot error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bots: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)

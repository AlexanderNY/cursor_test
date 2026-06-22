"""Роутер для агрегированных расписаний профилей."""

from fastapi import APIRouter, Request, Depends
from services.schedules_service import schedules_service
from services.schedule_service import schedule_service
from schemas import ScheduleResponse
from dependencies import get_admin_user
from typing import Dict


router = APIRouter(tags=["Schedules"])


@router.get("/schedules")
async def get_schedules():
    """Возвращает сводку расписаний из tg/tw/wp/vk_profiles.

    Используется scheduler для опроса изменений. Не требует x_user_id.
    """
    schedules = await schedules_service.get_all_schedules()
    return {"schedules": schedules}


@router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule(
    request: Request,
    admin_user: Dict = Depends(get_admin_user)
) -> ScheduleResponse:
    """Получает расписания из таблицы schedule_snapshots.
    
    Требует JWT аутентификации и роли admin.
    
    Returns:
        ScheduleResponse: Список расписаний из schedule_snapshots
    """
    schedules = await schedule_service.get_schedule_snapshots()
    return {"schedules": schedules}

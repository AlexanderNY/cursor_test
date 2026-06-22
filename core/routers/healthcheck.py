"""Роутер для проверки здоровья сервисов."""

from fastapi import APIRouter
from services.healthcheck_service import healthcheck_service
from schemas import HealthcheckResponse


router = APIRouter(tags=["Healthcheck"])


@router.get("/healthchecks", response_model=HealthcheckResponse)
async def get_healthchecks():
    """Проверяет здоровье всех микросервисов.
    
    Returns:
        HealthcheckResponse: Список результатов проверки
    """
    services = await healthcheck_service.check_all_services()
    return {"services": services}

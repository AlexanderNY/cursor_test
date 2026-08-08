"""Эндпоинт тестового запуска скрапинга по запросу."""

import logging

from fastapi import APIRouter, HTTPException

from schemas import RunRequest, RunResponse
from services.scraping_service import scrape_url_async
from services.url_safety import UnsafeUrlError, validate_public_http_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/run", tags=["Run"])


@router.post("", response_model=RunResponse)
async def run_scrape(request: RunRequest) -> RunResponse:
    """
    Запускает один сценарий скрапинга по запросу (без расписания).

    Открывает URL, находит элемент по XPath, возвращает текст и опционально скриншот элемента.
    """
    if not request.url or not request.xpath:
        raise HTTPException(status_code=400, detail="url and xpath are required")
    try:
        validate_public_http_url(request.url)
    except UnsafeUrlError as e:
        raise HTTPException(status_code=400, detail=f"URL not allowed: {e}") from e
    result = await scrape_url_async(
        request.url,
        request.xpath,
        request.take_screenshot,
        request.user_id,
    )
    return RunResponse(
        text=result.get("text"),
        screenshot_base64=result.get("screenshot_base64"),
        screenshot_path=result.get("screenshot_path"),
        error=result.get("error"),
    )

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import close_pool, init_pool
from app.routers import credentials, discoveries, runs, scenarios, sites
from app.schemas.models import HealthOut
from app.services.discovery_worker import start_discovery_worker, stop_discovery_worker
from app.services.worker import start_worker, stop_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("tester")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.artifacts_path.mkdir(parents=True, exist_ok=True)
    await init_pool()
    await start_worker()
    await start_discovery_worker()
    logger.info(
        "tester ready; TARGET_UI_URL=%s ARTIFACTS_DIR=%s",
        settings.TARGET_UI_URL,
        settings.ARTIFACTS_DIR,
    )
    yield
    await stop_discovery_worker()
    await stop_worker()
    await close_pool()


app = FastAPI(title="E2E Tester", version="0.3.0", lifespan=lifespan)
app.include_router(credentials.router)
app.include_router(sites.router)
app.include_router(scenarios.router)
app.include_router(runs.router)
app.include_router(discoveries.router)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@app.get("/api/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(
        status="ok",
        target_ui_url=settings.TARGET_UI_URL,
        target_api_url=settings.TARGET_API_URL,
        details={
            "artifacts_dir": settings.ARTIFACTS_DIR,
            "sqlite_path": str(settings.sqlite_path),
        },
    )


_assets_dir = WEB_DIR / "assets"
if WEB_DIR.is_dir() and _assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
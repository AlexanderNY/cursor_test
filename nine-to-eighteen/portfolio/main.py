"""9to18 portfolio-api: публичная страница кейсов."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import close_db, init_db
from routers import portfolio
from schema import PORTFOLIO_TABLES

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(PORTFOLIO_TABLES)
    yield
    await close_db()


app = FastAPI(
    title="9to18 Portfolio API",
    description="Публичная страница кейсов из Learn, Cert и GitHub",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(portfolio.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "portfolio-api"}


@app.exception_handler(Exception)
async def unhandled(request, exc):  # type: ignore[no-untyped-def]
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

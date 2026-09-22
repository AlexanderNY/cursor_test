"""9to18.ru independent API (site + learn)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import close_db, init_db
from schema import SITE_ALL_TABLES, SITE_SCHEMA_PATCHES
from routers import learn, site

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(SITE_ALL_TABLES + SITE_SCHEMA_PATCHES)
    try:
        from services.learn_service import learn_service

        inserted = await learn_service.ensure_seeded()
        if inserted:
            logger.info("Seeded %s learn posts", inserted)
    except Exception:
        logger.exception("Learn seed failed; continuing")
    yield
    await close_db()


app = FastAPI(
    title="9to18 Site API",
    description="Независимый API 9to18.ru: витрина, Learn, кабинет",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(site.router)
app.include_router(learn.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "site-api"}


@app.exception_handler(Exception)
async def unhandled(request, exc):  # type: ignore[no-untyped-def]
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

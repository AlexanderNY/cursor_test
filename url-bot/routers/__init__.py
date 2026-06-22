"""Роутеры url-bot."""

from .run import router as run_router
from .schedule import router as schedule_router

__all__ = ["run_router", "schedule_router"]

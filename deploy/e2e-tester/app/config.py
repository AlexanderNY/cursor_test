from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Single-file SQLite inside Docker volume (no separate Postgres)
    SQLITE_PATH: str = "/data/tester.db"
    DATA_DIR: str = "/data"
    TESTER_SECRET_KEY: str = ""
    TARGET_UI_URL: str = "https://www.copyparse.ru"
    TARGET_API_URL: str = ""
    ARTIFACTS_DIR: str = "/data/artifacts"

    @property
    def sqlite_path(self) -> Path:
        return Path(self.SQLITE_PATH)

    @property
    def artifacts_path(self) -> Path:
        return Path(self.ARTIFACTS_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()

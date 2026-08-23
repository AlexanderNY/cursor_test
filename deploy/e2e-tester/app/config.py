from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "dbname=tester user=tester password=tester host=tester-db"
    TESTER_SECRET_KEY: str = ""
    TARGET_UI_URL: str = "http://ui:8100"
    TARGET_API_URL: str = "http://gateway:8000"
    ARTIFACTS_DIR: str = "/data/artifacts"
    DB_POOL_MINSIZE: int = 1
    DB_POOL_MAXSIZE: int = 4

    @property
    def artifacts_path(self) -> Path:
        return Path(self.ARTIFACTS_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()

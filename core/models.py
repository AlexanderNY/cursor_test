"""SQL definitions for Core service tables."""

from shared.db.registry import get_platform_schemas
from shared.db.schemas.core import ALL_TABLES as CORE_TABLES

ALL_TABLES: list[str] = CORE_TABLES + get_platform_schemas()

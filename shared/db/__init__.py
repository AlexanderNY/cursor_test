"""Shared database schema contracts and DDL helpers."""

from shared.db.post_columns import POST_BASE_COLUMNS, POST_STATUS_CHECK, POST_STATUS_VALUES
from shared.db.post_model import (
    POST_CONTENT_STATUS_VALUES,
    POST_PLATFORMS,
    POST_TARGET_STATUS_VALUES,
    POST_TARGETS_TABLE_NAME,
    PUBLISH_PLATFORMS,
)
from shared.db.posts_repo import (
    InboundPostCreate,
    PostsRepository,
    PublishResult,
    UnknownPlatformError,
)

__all__ = [
    "InboundPostCreate",
    "POST_BASE_COLUMNS",
    "POST_CONTENT_STATUS_VALUES",
    "POST_PLATFORMS",
    "POST_STATUS_CHECK",
    "POST_STATUS_VALUES",
    "POST_TARGET_STATUS_VALUES",
    "POST_TARGETS_TABLE_NAME",
    "PUBLISH_PLATFORMS",
    "PostsRepository",
    "PublishResult",
    "UnknownPlatformError",
]

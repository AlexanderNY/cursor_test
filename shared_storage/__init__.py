"""
Единое файловое хранилище (S3-совместимое).
Используется core и ботами для загрузки/скачивания изображений.
"""

from .s3_storage import S3Storage, get_storage

__all__ = ["S3Storage", "get_storage"]

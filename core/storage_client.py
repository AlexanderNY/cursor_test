"""
Клиент единого хранилища (S3). Используется роутерами для загрузки и раздачи файлов.
При отсутствии конфигурации S3 возвращает None — роутеры могут использовать локальный fallback.
"""

import sys
from pathlib import Path

# Чтобы при запуске из корня репозитория (docker или python -m) находился shared_storage
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import settings

_storage = None


def get_storage():
    """Возвращает экземпляр S3Storage или None, если S3 не настроен."""
    global _storage
    if _storage is not None:
        return _storage
    if not settings.S3_BUCKET or not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
        return None
    try:
        from shared_storage import get_storage as _get_s3
        _storage = _get_s3(
            bucket=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
        )
        return _storage
    except Exception:
        return None

"""Проверка ключей объектов S3 для админских операций."""

from fastapi import HTTPException, status


def validate_storage_key(key: str) -> str:
    """Нормализует один ключ. Пустой ключ и выход за пределы бакета — 400."""
    normalized = (key or "").strip().lstrip("/")
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'key' is required and cannot be empty",
        )
    if ".." in normalized or normalized.startswith("\\"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage key",
        )
    return normalized


def validate_storage_keys(keys: list[str]) -> list[str]:
    """Нормализует список ключей для пакетного удаления. Дубликаты отбрасывает."""
    seen: set[str] = set()
    unique: list[str] = []
    for key in keys:
        storage_key = validate_storage_key(key)
        if storage_key in seen:
            continue
        seen.add(storage_key)
        unique.append(storage_key)
    if not unique:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one storage key is required",
        )
    return unique

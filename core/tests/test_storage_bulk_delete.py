"""Пакетное удаление объектов S3: разбор ответа и проверка ключей."""

import pytest
from fastapi import HTTPException

from storage_keys import validate_storage_keys
from shared_storage.s3_storage import collect_delete_objects_result


def test_collect_delete_objects_result_splits_deleted_and_errors():
    parsed = collect_delete_objects_result({
        "Deleted": [{"Key": "uploads/a.png"}, {"Key": "uploads/b.png"}],
        "Errors": [{"Key": "uploads/c.png", "Code": "AccessDenied", "Message": "denied"}],
    })
    assert parsed["deleted"] == ["uploads/a.png", "uploads/b.png"]
    assert parsed["failed"] == [{"key": "uploads/c.png", "error": "denied"}]


def test_validate_storage_keys_strips_and_dedupes():
    assert validate_storage_keys([" /uploads/a.png ", "uploads/a.png", "vk/b.jpg"]) == [
        "uploads/a.png",
        "vk/b.jpg",
    ]


def test_validate_storage_keys_rejects_traversal():
    with pytest.raises(HTTPException) as exc:
        validate_storage_keys(["uploads/../secret"])
    assert exc.value.status_code == 400

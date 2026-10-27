"""Backup file parse/export for Learn articles."""
from __future__ import annotations

import io
import json
import zipfile

import pytest

from services.learn_backup import build_export, parse_learn_backup


def test_export_roundtrip_drops_db_ids() -> None:
    payload = build_export(
        [
            {
                "id": 7,
                "slug": "algo-complexity",
                "title": "Сложность",
                "updatedAt": "2026-10-23T00:00:00+00:00",
                "createdAt": "2026-10-23T00:00:00+00:00",
                "publishedAt": "2026-10-23T10:00:00+03:00",
            }
        ]
    )
    posts = parse_learn_backup(json.dumps(payload).encode("utf-8"), "learn-articles.json")
    assert posts[0]["slug"] == "algo-complexity"
    assert "id" not in posts[0]
    assert payload["count"] == 1


def test_parse_seed_array_and_duplicate_slug() -> None:
    raw = json.dumps(
        [
            {"slug": "a", "title": "first"},
            {"slug": "a", "title": "second"},
        ]
    ).encode("utf-8")
    posts = parse_learn_backup(raw, "learn_seed.json")
    assert len(posts) == 1
    assert posts[0]["title"] == "second"


def test_parse_zip_prefers_learn_seed() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps({"articles": [{"slug": "nope", "title": "no"}]}),
        )
        archive.writestr(
            "learn_seed.json",
            json.dumps([{"slug": "pg-isolation", "title": "Изоляция"}]),
        )
    posts = parse_learn_backup(buffer.getvalue(), "learn-articles.zip")
    assert [item["slug"] for item in posts] == ["pg-isolation"]


def test_parse_rejects_empty_and_manifest_zip() -> None:
    with pytest.raises(ValueError, match="нет статей"):
        parse_learn_backup(b'{"posts": []}', "empty.json")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("manifest.json", "{}")
    with pytest.raises(ValueError, match="learn_seed.json"):
        parse_learn_backup(buffer.getvalue(), "backup.zip")

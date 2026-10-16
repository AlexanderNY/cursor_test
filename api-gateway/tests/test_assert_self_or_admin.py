"""Gateway self-or-admin binding helper."""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routers.bot_proxy import _assert_self_or_admin  # noqa: E402


def test_self_ok():
    _assert_self_or_admin({"user_id": 5, "role": "user"}, 5)


def test_admin_ok():
    _assert_self_or_admin({"user_id": 1, "role": "admin"}, 99)


def test_foreign_user_denied():
    with pytest.raises(HTTPException) as exc:
        _assert_self_or_admin({"user_id": 5, "role": "user"}, 6)
    assert exc.value.status_code == 403


def test_missing_user_denied():
    with pytest.raises(HTTPException) as exc:
        _assert_self_or_admin(None, 1)
    assert exc.value.status_code == 401

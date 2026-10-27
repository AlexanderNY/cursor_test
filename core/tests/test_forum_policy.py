"""Правила доступа форума без Postgres."""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

_POLICY = Path(__file__).resolve().parents[1] / "services" / "forum_policy.py"


def _load_policy():
    spec = importlib.util.spec_from_file_location("forum_policy_under_test", _POLICY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_policy()


def test_platform_thread_is_readable_without_membership():
    assert _mod.can_read_thread(scope="platform", group_id=None, is_member=False) is True


def test_workspace_thread_requires_membership():
    assert _mod.can_read_thread(scope="workspace", group_id=4, is_member=True) is True
    assert _mod.can_read_thread(scope="workspace", group_id=4, is_member=False) is False
    assert _mod.can_read_thread(scope="workspace", group_id=None, is_member=True) is False


def test_any_member_can_open_workspace_thread():
    assert _mod.can_open_thread(scope="workspace", workspace_role="viewer") is True
    assert _mod.can_open_thread(scope="workspace", workspace_role=None) is False
    assert _mod.can_open_thread(scope="platform", workspace_role=None) is True


def test_moderation_allows_author_owner_and_platform_admin():
    assert _mod.can_moderate(
        author_id=7, user_id=7, is_platform_admin=False, workspace_role="viewer"
    ) is True
    assert _mod.can_moderate(
        author_id=7, user_id=3, is_platform_admin=False, workspace_role="owner"
    ) is True
    assert _mod.can_moderate(
        author_id=7, user_id=3, is_platform_admin=False, workspace_role="admin"
    ) is True
    assert _mod.can_moderate(
        author_id=7, user_id=3, is_platform_admin=True, workspace_role="viewer"
    ) is True
    assert _mod.can_moderate(
        author_id=7, user_id=3, is_platform_admin=False, workspace_role="editor"
    ) is False
    assert _mod.can_moderate(
        author_id=0, user_id=3, is_platform_admin=False, workspace_role="editor"
    ) is False


def test_votes_only_on_open_suggestions():
    open_idea = _mod.thread_permissions(
        author_id=1,
        user_id=2,
        is_platform_admin=False,
        workspace_role=None,
        is_closed=False,
        kind="suggestion",
    )
    assert open_idea["can_vote"] is True
    assert open_idea["can_reply"] is True
    closed = _mod.thread_permissions(
        author_id=1,
        user_id=2,
        is_platform_admin=False,
        workspace_role=None,
        is_closed=True,
        kind="suggestion",
    )
    assert closed["can_vote"] is False
    assert closed["can_reply"] is False
    discussion = _mod.thread_permissions(
        author_id=1,
        user_id=1,
        is_platform_admin=False,
        workspace_role=None,
        is_closed=False,
        kind="discussion",
    )
    assert discussion["can_vote"] is False
    assert discussion["can_close"] is True


def test_clean_title_collapses_and_truncates():
    assert _mod.clean_title("  идея   недели  ") == "идея недели"
    assert _mod.clean_body("  текст  ") == "текст"
    assert _mod.clean_title("") == ""
    long_title = "а" * 300
    assert len(_mod.clean_title(long_title)) == 255


def test_parse_scope_and_kind():
    assert _mod.parse_scope(" Platform ") == "platform"
    assert _mod.parse_scope("nope") is None
    assert _mod.parse_kind_filter(None) == (True, None)
    assert _mod.parse_kind_filter(" suggestion ") == (True, "suggestion")
    assert _mod.parse_kind_filter("nope") == (False, None)


def test_thread_from_row_maps_fields():
    created = datetime(2026, 10, 27, tzinfo=timezone.utc)
    row = (
        9,
        "platform",
        None,
        None,
        "suggestion",
        "Тёмная тема",
        "Переключатель в профиле",
        4,
        "anna",
        False,
        3,
        True,
        1,
        created,
        created,
        "/core/forum/avatars/4",
    )
    item = _mod.thread_from_row(row)
    assert item["id"] == 9
    assert item["scope"] == "platform"
    assert item["group_id"] is None
    assert item["vote_count"] == 3
    assert item["voted"] is True
    assert item["author_name"] == "anna"
    assert item["author_avatar"] == "/core/forum/avatars/4"


def test_sniff_image_type_accepts_png_and_rejects_text():
    png = b"\x89PNG\r\n\x1a\n" + b"rest"
    assert _mod.sniff_image_type(png) == "image/png"
    assert _mod.sniff_image_type(b"not an image") is None
    assert _mod.avatar_public_path(4) == "/core/forum/avatars/4"

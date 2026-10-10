"""Unit tests for WordPress collect cursor planning."""

from datetime import datetime, timezone

from services.collect_cursor import (
    CollectCursor,
    merge_cursor_advance,
    newest_cursor_from_posts,
    plan_collect_query,
    plan_next_page,
    query_params_from_plan,
    should_skip_seen_post,
    to_wp_after_param,
)


def _post(wp_id: int, date_gmt: str, link: str = "") -> dict:
    return {
        "id": wp_id,
        "date_gmt": date_gmt,
        "link": link or f"https://example.com/?p={wp_id}",
        "title": {"rendered": f"Post {wp_id}"},
        "content": {"rendered": f"Body {wp_id}"},
    }


def test_bootstrap_plan_is_single_page_newest():
    plan = plan_collect_query(None, remaining=10)
    assert plan.order == "desc"
    assert plan.per_page == 10
    assert plan.after is None
    assert plan.allow_next_page is False
    assert plan_next_page(plan, posts_on_page=10, remaining_after_page=5) is None

    params = query_params_from_plan(plan)
    assert "after" not in params
    assert params["order"] == "desc"
    assert "_fields" in params
    assert "id" in params["_fields"]


def test_bootstrap_clamps_per_page():
    plan = plan_collect_query(None, remaining=100)
    assert plan.per_page == 10
    plan2 = plan_collect_query(None, remaining=3)
    assert plan2.per_page == 3


def test_incremental_plan_uses_after_minus_one_second():
    cursor = CollectCursor(
        after_gmt=datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc),
        last_wp_id=42,
        bootstrapped=True,
    )
    plan = plan_collect_query(cursor, remaining=10)
    assert plan.order == "asc"
    assert plan.allow_next_page is True
    assert plan.after == "2026-10-08T11:59:59"
    params = query_params_from_plan(plan)
    assert params["after"] == "2026-10-08T11:59:59"


def test_incremental_can_page_when_full():
    cursor = CollectCursor(
        after_gmt=datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc),
        last_wp_id=1,
        bootstrapped=True,
    )
    plan = plan_collect_query(cursor, remaining=10)
    nxt = plan_next_page(plan, posts_on_page=10, remaining_after_page=7)
    assert nxt is not None
    assert nxt.page == 2
    assert nxt.per_page == 7
    assert nxt.after == plan.after

    assert plan_next_page(plan, posts_on_page=3, remaining_after_page=7) is None
    assert plan_next_page(plan, posts_on_page=10, remaining_after_page=0) is None


def test_newest_cursor_and_advance():
    posts = [
        _post(1, "2026-10-01T10:00:00"),
        _post(3, "2026-10-08T15:00:00"),
        _post(2, "2026-10-08T12:00:00"),
    ]
    newest = newest_cursor_from_posts(posts)
    assert newest is not None
    assert newest.last_wp_id == 3
    assert newest.after_gmt == datetime(2026, 10, 8, 15, 0, 0, tzinfo=timezone.utc)
    assert newest.bootstrapped is True

    advanced = merge_cursor_advance(None, posts, force_bootstrap=True)
    assert advanced == newest

    same = merge_cursor_advance(newest, [_post(2, "2026-10-08T12:00:00")])
    assert same == newest

    later = merge_cursor_advance(
        newest,
        [_post(9, "2026-10-09T01:00:00")],
    )
    assert later is not None
    assert later.last_wp_id == 9


def test_force_bootstrap_empty_site():
    cursor = merge_cursor_advance(None, [], force_bootstrap=True)
    assert cursor is not None
    assert cursor.bootstrapped is True
    assert cursor.after_gmt is None


def test_should_skip_seen_post_same_second_and_id():
    cursor = CollectCursor(
        after_gmt=datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc),
        last_wp_id=42,
        bootstrapped=True,
    )
    assert should_skip_seen_post(_post(42, "2026-10-08T12:00:00"), cursor)
    assert should_skip_seen_post(_post(40, "2026-10-08T12:00:00"), cursor)
    assert not should_skip_seen_post(_post(43, "2026-10-08T12:00:00"), cursor)
    assert not should_skip_seen_post(_post(50, "2026-10-08T12:00:01"), cursor)
    assert should_skip_seen_post(_post(99, "2026-10-08T11:59:00"), cursor)


def test_to_wp_after_param():
    dt = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert to_wp_after_param(dt) == "2026-01-02T03:04:05"


def test_page_target_extras_override_channel():
    from services.publish_service import _page_target_from_sources

    page_id, slug = _page_target_from_sources(
        extras={"wp_page_id": 7, "wp_page_slug": "from-post"},
        channel_processing={"wp_page_id": 99, "wp_page_slug": "from-channel"},
    )
    assert page_id == 7
    assert slug == "from-post"

    page_id, slug = _page_target_from_sources(
        extras={},
        channel_processing={"wp_page_slug": "about"},
    )
    assert page_id is None
    assert slug == "about"

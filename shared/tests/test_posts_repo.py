import pytest

from shared.db.post_model import POST_TARGETS_TABLE_NAME
from shared.db.posts_repo import (
    CLAIM_PROCESS_COLUMNS,
    InboundPostCreate,
    PostsRepository,
    PublishResult,
    UnknownPlatformError,
    claim_process_select_sql,
    claim_publish_select_sql,
    create_inbound_sql,
    ensure_targets_sql,
    list_targets_sql,
    mark_posts_status_sql,
    mark_targets_status_sql,
    publish_result_sql,
    require_publish_platform,
)
from shared.status_lease import DEFAULT_STALE_PUBLISHING_MINUTES


class _Col:
    def __init__(self, name: str) -> None:
        self.name = name


class RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.fetchall_queue: list[list[tuple]] = []
        self.fetchone_queue: list[tuple | None] = []
        self.description: list[_Col] = []
        self.rowcount = 0

    async def execute(self, sql: str, params=None) -> None:
        self.calls.append((sql, params))

    async def fetchall(self) -> list[tuple]:
        if not self.fetchall_queue:
            return []
        return self.fetchall_queue.pop(0)

    async def fetchone(self) -> tuple | None:
        if not self.fetchone_queue:
            return None
        return self.fetchone_queue.pop(0)


def test_create_inbound_sql_writes_posts_not_platform_tables():
    sql, params = create_inbound_sql(
        InboundPostCreate(
            user_id=7,
            source_platform="Telegram",
            post_text="hello",
            extras={"vk_source_id": 1},
            images=["a.jpg"],
        )
    )
    assert "INSERT INTO posts" in sql
    assert "tg_posts" not in sql
    assert "to_tg" not in sql
    assert params[0] == 7
    assert params[3] == "tg"
    assert params[-1] == "collected"
    assert "vk_source_id" in params[-4]


def test_ensure_targets_sql_binds_platform_not_table():
    sql, params = ensure_targets_sql(
        post_id=3,
        user_id=9,
        platforms=["vk", "telegram"],
        status="ready",
    )
    assert f"INSERT INTO {POST_TARGETS_TABLE_NAME}" in sql
    assert "ON CONFLICT (post_id, platform)" in sql
    assert "vk_posts" not in sql
    assert "SET status = EXCLUDED.status" in sql
    assert params == [
        3, 9, "vk", "ready", "[]", "[]",
        3, 9, "tg", "ready", "[]", "[]",
    ]


def test_claim_process_select_skips_locks_on_posts():
    sql, params = claim_process_select_sql(limit=10)
    assert "FROM posts" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "status IN ('collected', 'created')" in sql
    assert params == (10,)
    for column in CLAIM_PROCESS_COLUMNS:
        assert column in sql


def test_claim_publish_select_binds_platform():
    sql, params = claim_publish_select_sql(platform="instagram", limit=5, user_id=2)
    assert "FROM post_targets t" in sql
    assert "JOIN posts p" in sql
    assert "FOR UPDATE OF t SKIP LOCKED" in sql
    assert "t.platform = %s" in sql
    assert "instagram_posts" not in sql
    assert "%s" in sql
    assert params == ("instagram", "ready", 2, 5)


def test_claim_publish_rejects_unknown_and_non_publish_platforms():
    with pytest.raises(UnknownPlatformError):
        claim_publish_select_sql(platform="tg_posts", limit=1)
    with pytest.raises(UnknownPlatformError):
        require_publish_platform("cpost")
    with pytest.raises(UnknownPlatformError):
        require_publish_platform("url")


def test_mark_status_sql_uses_bind_ids():
    sql, params = mark_posts_status_sql([1, 2, 3], "processing")
    assert "UPDATE posts" in sql
    assert params == ("processing", 1, 2, 3)
    target_sql, target_params = mark_targets_status_sql([9], "publishing")
    assert f"UPDATE {POST_TARGETS_TABLE_NAME}" in target_sql
    assert target_params == ("publishing", 9)


def test_publish_result_sql_only_updates_publishing_row():
    sql, params = publish_result_sql(
        PublishResult(target_id=44, ok=True, result={"remote_id": "abc"})
    )
    assert f"UPDATE {POST_TARGETS_TABLE_NAME}" in sql
    assert "status = 'publishing'" in sql
    assert "%s::jsonb" in sql
    assert params[0] == "published"
    assert params[2] == 44
    failed_sql, failed_params = publish_result_sql(PublishResult(target_id=1, ok=False))
    assert failed_params[0] == "failed"
    assert "error" in failed_params[1]
    skipped_sql, skipped_params = publish_result_sql(
        PublishResult(target_id=2, ok=False, status="skipped")
    )
    assert skipped_params[0] == "skipped"


def test_list_targets_sql_joins_hub_and_filters_platform():
    sql, params = list_targets_sql(user_id=3, platform="tg", limit=10, offset=5)
    assert "JOIN posts p" in sql
    assert "t.platform = %s" in sql
    assert params[0] == 3
    assert params[1] == "tg"
    assert params[-2:] == (10, 5)


@pytest.mark.asyncio
async def test_repository_claim_publish_records_reclaim_select_update():
    cur = RecordingCursor()
    cur.description = [
        _Col(name)
        for name in (
            "target_id",
            "post_id",
            "user_id",
            "platform",
            "status",
            "publish_at",
            "target_channels",
            "target_groups",
            "result",
            "post_text",
            "images",
            "videos",
            "title",
            "url",
            "extras",
            "platform_texts",
            "brand_id",
            "channel_id",
        )
    ]
    cur.fetchall_queue = [
        [
            (
                11,
                20,
                3,
                "tg",
                "ready",
                None,
                "[]",
                "[]",
                "{}",
                "hi",
                "[]",
                "[]",
                None,
                None,
                "{}",
                "{}",
                None,
                None,
            )
        ]
    ]
    repo = PostsRepository(cur)
    claimed = await repo.claim_publish(platform="tg", limit=4)

    assert len(claimed) == 1
    assert claimed[0]["target_id"] == 11
    assert claimed[0]["status"] == "publishing"
    assert len(cur.calls) == 3
    reclaim_sql, reclaim_params = cur.calls[0]
    assert f"UPDATE {POST_TARGETS_TABLE_NAME}" in reclaim_sql
    assert reclaim_params == ("ready", "publishing", DEFAULT_STALE_PUBLISHING_MINUTES)
    select_sql, select_params = cur.calls[1]
    assert "FOR UPDATE OF t SKIP LOCKED" in select_sql
    assert select_params[0] == "tg"
    update_sql, update_params = cur.calls[2]
    assert update_params[0] == "publishing"
    assert update_params[1] == 11


@pytest.mark.asyncio
async def test_repository_claim_process_then_complete():
    cur = RecordingCursor()
    cur.description = [_Col(name) for name in CLAIM_PROCESS_COLUMNS]
    cur.fetchall_queue = [
        [(5, 1, "vk", None, "text", "[]", None, "{}", "{}", "collected") + (False,) * 7]
    ]
    repo = PostsRepository(cur)
    claimed = await repo.claim_process(limit=2)
    assert claimed[0]["id"] == 5
    assert claimed[0]["status"] == "processing"
    await repo.complete_processing([5], "ready")
    last_sql, last_params = cur.calls[-1]
    assert "UPDATE posts" in last_sql
    assert last_params == ("ready", 5)


@pytest.mark.asyncio
async def test_repository_create_inbound_with_targets():
    cur = RecordingCursor()
    cur.description = [_Col("id"), _Col("user_id"), _Col("source_platform"), _Col("status")]
    cur.fetchone_queue = [(15, 2, "url", "collected")]
    cur.fetchall_queue = [[(1, 15, "tg", "pending"), (2, 15, "vk", "pending")]]
    repo = PostsRepository(cur)
    created = await repo.create_inbound(
        InboundPostCreate(
            user_id=2,
            source_platform="url",
            post_text="x",
            target_platforms=("tg", "vk"),
        )
    )
    assert created["id"] == 15
    assert [item["platform"] for item in created["targets"]] == ["tg", "vk"]
    insert_sql, _ = cur.calls[0]
    assert "INSERT INTO posts" in insert_sql
    target_sql, target_params = cur.calls[1]
    assert "INSERT INTO post_targets" in target_sql
    assert "tg" in target_params
    assert "vk" in target_params


@pytest.mark.asyncio
async def test_apply_publish_result_returns_row():
    cur = RecordingCursor()
    cur.description = [
        _Col("id"),
        _Col("post_id"),
        _Col("platform"),
        _Col("status"),
        _Col("result"),
    ]
    cur.fetchone_queue = [(11, 20, "tg", "published", {"remote_id": "1"})]
    repo = PostsRepository(cur)
    updated = await repo.apply_publish_result(
        PublishResult(target_id=11, ok=True, result={"remote_id": "1"})
    )
    assert updated is not None
    assert updated["status"] == "published"
    sql, params = cur.calls[0]
    assert params[0] == "published"
    assert params[2] == 11
    assert "publishing" in sql


def test_resolve_publish_platforms_prefers_legacy_flags():
    from shared.db.posts_repo import resolve_publish_platforms

    assert resolve_publish_platforms(
        legacy_flags={"to_vk": True, "to_tg": False},
        process_services=["telegram"],
        source_platform="tg",
    ) == ["vk"]


def test_resolve_publish_platforms_from_services_and_tg_default():
    from shared.db.posts_repo import resolve_publish_platforms

    assert resolve_publish_platforms(
        legacy_flags={},
        process_services=["wordpress", "instagram"],
        source_platform="url",
    ) == ["wp", "instagram"]
    assert resolve_publish_platforms(
        legacy_flags={},
        process_services=[],
        source_platform="tg",
    ) == ["tg"]
    assert resolve_publish_platforms(
        legacy_flags={},
        process_services=[],
        source_platform="vk",
    ) == []


def test_save_processed_sql_updates_hub_only():
    from shared.db.posts_repo import save_processed_sql

    sql, params = save_processed_sql(
        post_id=8,
        text="hi",
        images=[],
        platform_texts={"telegram": "hi"},
        status="ready",
    )
    assert "UPDATE posts" in sql
    assert "status = 'processing'" in sql
    assert "to_tg" not in sql
    assert "tg_posts" not in sql
    assert params[0] == "hi"
    assert params[-1] == 8

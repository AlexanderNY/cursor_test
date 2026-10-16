"""Pure helpers for WordPress collect cursor (bootstrap window + after)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence


POST_FIELDS = "id,date_gmt,link,title,content,slug"
DEFAULT_MAX_PER_PAGE = 10


@dataclass(frozen=True)
class CollectCursor:
    """Persisted collect position for (user_id, site_url)."""

    after_gmt: Optional[datetime]
    last_wp_id: Optional[int]
    bootstrapped: bool = False


@dataclass(frozen=True)
class CollectQueryPlan:
    """One GET /wp/v2/posts request plan."""

    per_page: int
    order: str  # desc | asc
    orderby: str
    after: Optional[str] = None
    page: int = 1
    status: str = "publish"
    fields: str = POST_FIELDS
    allow_next_page: bool = False


def _clamp_per_page(remaining: int, max_per_page: int = DEFAULT_MAX_PER_PAGE) -> int:
    return max(1, min(int(remaining), int(max_per_page)))


def parse_wp_datetime(value: Any) -> Optional[datetime]:
    """Parse WordPress date_gmt / date string to aware UTC datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_wp_after_param(dt: datetime) -> str:
    """Format datetime for WP REST `after` query (ISO 8601 UTC)."""
    aware = parse_wp_datetime(dt) or dt
    return aware.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def plan_collect_query(
    cursor: Optional[CollectCursor],
    *,
    remaining: int,
    max_per_page: int = DEFAULT_MAX_PER_PAGE,
) -> CollectQueryPlan:
    """
    Build the first request for a collect pass.

    - No cursor / not bootstrapped: newest N posts, single page only.
    - Bootstrapped: posts after (cursor.after_gmt - 1s), ascending, may page.
    """
    per_page = _clamp_per_page(remaining, max_per_page)
    if cursor is None or not cursor.bootstrapped or cursor.after_gmt is None:
        return CollectQueryPlan(
            per_page=per_page,
            order="desc",
            orderby="date",
            after=None,
            page=1,
            allow_next_page=False,
        )
    after_dt = cursor.after_gmt - timedelta(seconds=1)
    return CollectQueryPlan(
        per_page=per_page,
        order="asc",
        orderby="date",
        after=to_wp_after_param(after_dt),
        page=1,
        allow_next_page=True,
    )


def plan_next_page(
    plan: CollectQueryPlan,
    *,
    posts_on_page: int,
    remaining_after_page: int,
) -> Optional[CollectQueryPlan]:
    """Return next page plan when still paging and page was full."""
    if not plan.allow_next_page:
        return None
    if remaining_after_page <= 0:
        return None
    if posts_on_page < plan.per_page:
        return None
    return CollectQueryPlan(
        per_page=_clamp_per_page(remaining_after_page, plan.per_page),
        order=plan.order,
        orderby=plan.orderby,
        after=plan.after,
        page=plan.page + 1,
        status=plan.status,
        fields=plan.fields,
        allow_next_page=True,
    )


def wp_field_text(value: Any) -> str:
    """Prefer REST `raw` (context=edit) over rendered HTML."""
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, str) and raw != "":
            return raw
        rendered = value.get("rendered")
        if isinstance(rendered, str):
            return rendered
        return ""
    if value is None:
        return ""
    return str(value)


def post_wp_id(post: Dict[str, Any]) -> Optional[int]:
    raw = post.get("id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def post_date_gmt(post: Dict[str, Any]) -> Optional[datetime]:
    return parse_wp_datetime(post.get("date_gmt") or post.get("date"))


def newest_cursor_from_posts(posts: Sequence[Dict[str, Any]]) -> Optional[CollectCursor]:
    """Cursor pointing at the newest post in the list (by date_gmt, then id)."""
    best_dt: Optional[datetime] = None
    best_id: Optional[int] = None
    for post in posts:
        dt = post_date_gmt(post)
        wp_id = post_wp_id(post)
        if dt is None:
            continue
        if best_dt is None or dt > best_dt or (dt == best_dt and (wp_id or 0) > (best_id or 0)):
            best_dt = dt
            best_id = wp_id
    if best_dt is None:
        return None
    return CollectCursor(after_gmt=best_dt, last_wp_id=best_id, bootstrapped=True)


def should_skip_seen_post(
    post: Dict[str, Any],
    cursor: Optional[CollectCursor],
) -> bool:
    """Skip posts already covered by cursor when using after= (same-second overlap)."""
    if cursor is None or not cursor.bootstrapped or cursor.after_gmt is None:
        return False
    wp_id = post_wp_id(post)
    dt = post_date_gmt(post)
    if wp_id is not None and cursor.last_wp_id is not None and wp_id == cursor.last_wp_id:
        return True
    if dt is not None and dt < cursor.after_gmt:
        return True
    if (
        dt is not None
        and cursor.last_wp_id is not None
        and dt == cursor.after_gmt
        and wp_id is not None
        and wp_id <= cursor.last_wp_id
    ):
        return True
    return False


def merge_cursor_advance(
    current: Optional[CollectCursor],
    posts: Sequence[Dict[str, Any]],
    *,
    force_bootstrap: bool = False,
) -> Optional[CollectCursor]:
    """
    Advance cursor to newest post among seen posts.

    On bootstrap (force_bootstrap), set cursor even when no posts were saved
    (empty site or all filtered) only if posts were returned from WP.
    """
    from_posts = newest_cursor_from_posts(posts)
    if from_posts is None:
        if force_bootstrap and current is None:
            return CollectCursor(after_gmt=None, last_wp_id=None, bootstrapped=True)
        if force_bootstrap and current is not None and not current.bootstrapped:
            return CollectCursor(
                after_gmt=current.after_gmt,
                last_wp_id=current.last_wp_id,
                bootstrapped=True,
            )
        return current
    if current is None or not current.bootstrapped or current.after_gmt is None:
        return from_posts
    if from_posts.after_gmt is None:
        return current
    if from_posts.after_gmt > current.after_gmt:
        return from_posts
    if from_posts.after_gmt == current.after_gmt:
        cur_id = current.last_wp_id or 0
        new_id = from_posts.last_wp_id or 0
        if new_id > cur_id:
            return from_posts
    return CollectCursor(
        after_gmt=current.after_gmt,
        last_wp_id=current.last_wp_id,
        bootstrapped=True,
    )


def query_params_from_plan(plan: CollectQueryPlan) -> Dict[str, Any]:
    """httpx params dict for WordPressClient.get_posts."""
    params: Dict[str, Any] = {
        "per_page": plan.per_page,
        "page": plan.page,
        "status": plan.status,
        "orderby": plan.orderby,
        "order": plan.order,
        "_fields": plan.fields,
    }
    if plan.after:
        params["after"] = plan.after
    return params

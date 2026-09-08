"""Content calendar series (рубрики): recurring slot templates materialized as jobs."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta, time
from typing import Any, Optional

from database import get_db_connection, release_db_connection
from services.quota_service import (
    ensure_smm_limit,
    get_user_tariff,
    plan_limit,
)
from services.smm_service import smm_service

logger = logging.getLogger(__name__)

MAX_TITLE = 255
MAX_BODY = 20000
TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
CADENCES = frozenset({"weekly", "biweekly"})
MUTABLE_JOB_STATUSES = frozenset({"draft", "scheduled", "ready", "pending_approval"})

SERIES_SELECT = """
id, user_id, brand_id, title, color, body, template_id, targets,
weekdays, publish_time, cadence, is_active, starts_on, ends_on,
created_at, updated_at
"""


def _parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def _iso_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _iso_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def _sanitize_targets(raw: Any) -> list[dict[str, Any]]:
    data = _parse_json_field(raw, [])
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for item in data[:20]:
        if not isinstance(item, dict):
            continue
        network = str(item.get("network") or "").strip().lower()[:20]
        external_id = str(item.get("external_id") or "").strip()[:128]
        if not network or not external_id:
            continue
        out.append({"network": network, "external_id": external_id})
    return out


def _sanitize_weekdays(raw: Any) -> list[int]:
    data = _parse_json_field(raw, [])
    if not isinstance(data, list):
        return []
    out: list[int] = []
    for item in data:
        try:
            day = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= day <= 7 and day not in out:
            out.append(day)
    return sorted(out)


def _sanitize_color(raw: Any) -> str:
    color = str(raw or "#8B5CF6").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        return color.upper()
    return "#8B5CF6"


def _sanitize_publish_time(raw: Any) -> str:
    text = str(raw or "10:00").strip()
    match = TIME_RE.match(text)
    if not match:
        return "10:00"
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def _parse_date(raw: Any) -> Optional[date]:
    if raw is None or raw == "":
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    text = str(raw).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _row_series(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "title": r[3],
        "color": r[4] or "#8B5CF6",
        "body": r[5] or "",
        "template_id": r[6],
        "targets": _sanitize_targets(r[7]),
        "weekdays": _sanitize_weekdays(r[8]),
        "publish_time": _sanitize_publish_time(r[9]),
        "cadence": r[10] if r[10] in CADENCES else "weekly",
        "is_active": bool(r[11]),
        "starts_on": _iso_date(r[12]),
        "ends_on": _iso_date(r[13]),
        "created_at": _iso_dt(r[14]),
        "updated_at": _iso_dt(r[15]),
    }


def _occurrence_dates(
    *,
    weekdays: list[int],
    cadence: str,
    starts_on: Optional[date],
    ends_on: Optional[date],
    horizon_end: date,
    today: date,
) -> list[date]:
    if not weekdays:
        return []
    start = starts_on or today
    if start < today:
        start = today
    end = horizon_end
    if ends_on and ends_on < end:
        end = ends_on
    if start > end:
        return []

    anchor = starts_on or today
    out: list[date] = []
    cur = start
    while cur <= end:
        if cur.isoweekday() in weekdays:
            if cadence == "biweekly":
                weeks = (cur - anchor).days // 7
                if weeks % 2 != 0:
                    cur += timedelta(days=1)
                    continue
            out.append(cur)
        cur += timedelta(days=1)
    return out


def _combine_publish_at(day: date, publish_time: str) -> datetime:
    hh, mm = _sanitize_publish_time(publish_time).split(":")
    return datetime.combine(day, time(int(hh), int(mm)))


class ContentSeriesService:
    async def _require_brand(self, user_id: int, brand_id: int) -> dict:
        brand = await smm_service.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        return brand

    async def count_series(self, user_id: int) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM smm_content_series WHERE user_id = %s",
                    (user_id,),
                )
                row = await cur.fetchone()
                return int(row[0] if row else 0)
        finally:
            await release_db_connection(conn)

    async def get_series(self, user_id: int, series_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {SERIES_SELECT}
                    FROM smm_content_series
                    WHERE id = %s
                    """,
                    (series_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                series = _row_series(row)
        finally:
            await release_db_connection(conn)
        brand = await smm_service.get_brand(user_id, series["brand_id"])
        if not brand:
            return None
        return series

    async def list_series(
        self,
        user_id: int,
        brand_id: int,
        *,
        active_only: bool = False,
    ) -> list[dict]:
        brand = await self._require_brand(user_id, brand_id)
        owner_id = int(brand.get("user_id") or user_id)
        conditions = ["user_id = %s", "brand_id = %s"]
        params: list[Any] = [owner_id, brand_id]
        if active_only:
            conditions.append("is_active = TRUE")
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {SERIES_SELECT}
                    FROM smm_content_series
                    WHERE {where}
                    ORDER BY title, id
                    LIMIT 200
                    """,
                    params,
                )
                rows = await cur.fetchall()
                return [_row_series(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def create_series(
        self,
        user_id: int,
        brand_id: int,
        *,
        title: str,
        color: str = "#8B5CF6",
        body: str = "",
        template_id: Optional[int] = None,
        targets: Optional[list[dict]] = None,
        weekdays: Optional[list[int]] = None,
        publish_time: str = "10:00",
        cadence: str = "weekly",
        is_active: bool = True,
        starts_on: Optional[str] = None,
        ends_on: Optional[str] = None,
        expand: bool = True,
    ) -> dict:
        brand = await self._require_brand(user_id, brand_id)
        used = await self.count_series(user_id)
        await ensure_smm_limit(user_id, "max_content_series", used, units=1)

        title_clean = (title or "").strip()[:MAX_TITLE]
        if not title_clean:
            raise ValueError("Title is required")
        cadence_clean = (cadence or "weekly").strip().lower()
        if cadence_clean not in CADENCES:
            raise ValueError("cadence must be weekly or biweekly")
        weekdays_clean = _sanitize_weekdays(weekdays)
        if not weekdays_clean:
            raise ValueError("At least one weekday (1=Mon … 7=Sun) is required")
        targets_clean = _sanitize_targets(targets)
        body_clean = (body or "")[:MAX_BODY]
        if template_id is not None:
            tpl = await self._get_template(user_id, int(template_id))
            if not tpl or tpl.get("brand_id") != brand_id:
                raise ValueError("template_id not found for brand")
            if not body_clean and tpl.get("kind") == "post_body":
                body_clean = str(tpl.get("body") or "")[:MAX_BODY]
        if not body_clean:
            body_clean = title_clean

        starts = _parse_date(starts_on) or date.today()
        ends = _parse_date(ends_on)
        if ends and ends < starts:
            raise ValueError("ends_on must be on or after starts_on")

        owner_id = int(brand.get("user_id") or user_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    INSERT INTO smm_content_series (
                        user_id, brand_id, title, color, body, template_id, targets,
                        weekdays, publish_time, cadence, is_active, starts_on, ends_on
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s::jsonb,
                        %s::jsonb, %s, %s, %s, %s, %s
                    )
                    RETURNING {SERIES_SELECT}
                    """,
                    (
                        owner_id,
                        brand_id,
                        title_clean,
                        _sanitize_color(color),
                        body_clean,
                        template_id,
                        json.dumps(targets_clean, ensure_ascii=False),
                        json.dumps(weekdays_clean),
                        _sanitize_publish_time(publish_time),
                        cadence_clean,
                        bool(is_active),
                        starts,
                        ends,
                    ),
                )
                row = await cur.fetchone()
                series = _row_series(row)
        finally:
            await release_db_connection(conn)

        if expand and series.get("is_active"):
            await self.expand_series(user_id, series["id"])
            refreshed = await self.get_series(user_id, series["id"])
            return refreshed or series
        return series

    async def update_series(
        self,
        user_id: int,
        series_id: int,
        *,
        title: Optional[str] = None,
        color: Optional[str] = None,
        body: Optional[str] = None,
        template_id: Optional[int] = None,
        clear_template: bool = False,
        targets: Optional[list[dict]] = None,
        weekdays: Optional[list[int]] = None,
        publish_time: Optional[str] = None,
        cadence: Optional[str] = None,
        is_active: Optional[bool] = None,
        starts_on: Optional[str] = None,
        ends_on: Optional[str] = None,
        rebuild: bool = True,
    ) -> Optional[dict]:
        series = await self.get_series(user_id, series_id)
        if not series:
            return None

        new_title = series["title"]
        if title is not None:
            new_title = title.strip()[:MAX_TITLE]
            if not new_title:
                raise ValueError("Title is required")
        new_color = _sanitize_color(color) if color is not None else series["color"]
        new_body = series["body"]
        if body is not None:
            new_body = body[:MAX_BODY]
        new_template_id = series.get("template_id")
        if clear_template:
            new_template_id = None
        elif template_id is not None:
            tpl = await self._get_template(user_id, int(template_id))
            if not tpl or tpl.get("brand_id") != series["brand_id"]:
                raise ValueError("template_id not found for brand")
            new_template_id = int(template_id)
        new_targets = (
            _sanitize_targets(targets) if targets is not None else series["targets"]
        )
        new_weekdays = (
            _sanitize_weekdays(weekdays) if weekdays is not None else series["weekdays"]
        )
        if not new_weekdays:
            raise ValueError("At least one weekday (1=Mon … 7=Sun) is required")
        new_time = (
            _sanitize_publish_time(publish_time)
            if publish_time is not None
            else series["publish_time"]
        )
        new_cadence = series["cadence"]
        if cadence is not None:
            c = cadence.strip().lower()
            if c not in CADENCES:
                raise ValueError("cadence must be weekly or biweekly")
            new_cadence = c
        new_active = series["is_active"] if is_active is None else bool(is_active)
        new_starts = (
            _parse_date(starts_on)
            if starts_on is not None
            else _parse_date(series.get("starts_on"))
        )
        new_ends = (
            _parse_date(ends_on)
            if ends_on is not None
            else _parse_date(series.get("ends_on"))
        )
        if new_starts and new_ends and new_ends < new_starts:
            raise ValueError("ends_on must be on or after starts_on")

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_content_series SET
                        title = %s,
                        color = %s,
                        body = %s,
                        template_id = %s,
                        targets = %s::jsonb,
                        weekdays = %s::jsonb,
                        publish_time = %s,
                        cadence = %s,
                        is_active = %s,
                        starts_on = %s,
                        ends_on = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING {SERIES_SELECT}
                    """,
                    (
                        new_title,
                        new_color,
                        new_body,
                        new_template_id,
                        json.dumps(new_targets, ensure_ascii=False),
                        json.dumps(new_weekdays),
                        new_time,
                        new_cadence,
                        new_active,
                        new_starts,
                        new_ends,
                        series_id,
                    ),
                )
                row = await cur.fetchone()
                updated = _row_series(row) if row else None
        finally:
            await release_db_connection(conn)

        if not updated:
            return None

        if not updated["is_active"]:
            await self._cancel_future_instances(int(updated["user_id"]), series_id)
        elif rebuild:
            await self._cancel_future_instances(int(updated["user_id"]), series_id)
            await self.expand_series(user_id, series_id)
        return await self.get_series(user_id, series_id)

    async def delete_series(self, user_id: int, series_id: int) -> bool:
        series = await self.get_series(user_id, series_id)
        if not series:
            return False
        owner_id = int(series["user_id"])
        await self._cancel_future_instances(owner_id, series_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_content_series WHERE id = %s",
                    (series_id,),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def expand_series(
        self,
        user_id: int,
        series_id: int,
        *,
        horizon_days: Optional[int] = None,
    ) -> dict[str, Any]:
        series = await self.get_series(user_id, series_id)
        if not series:
            raise ValueError("Series not found")
        if not series.get("is_active"):
            return {"created": 0, "job_ids": [], "skipped": 0}

        tariff = await get_user_tariff(user_id)
        horizon = horizon_days
        if horizon is None:
            horizon = plan_limit(tariff, "schedule_horizon_days", 7)
        today = date.today()
        horizon_end = today + timedelta(days=int(horizon))
        starts = _parse_date(series.get("starts_on"))
        ends = _parse_date(series.get("ends_on"))
        days = _occurrence_dates(
            weekdays=series["weekdays"],
            cadence=series["cadence"],
            starts_on=starts,
            ends_on=ends,
            horizon_end=horizon_end,
            today=today,
        )
        existing = await self._existing_instance_dates(series_id)
        created_ids: list[int] = []
        skipped = 0
        for day in days:
            if day in existing:
                skipped += 1
                continue
            pub_at = _combine_publish_at(day, series["publish_time"])
            job = await self._create_instance_job(
                user_id=user_id,
                series=series,
                publish_at=pub_at,
            )
            if job:
                created_ids.append(int(job["id"]))
                existing.add(day)
            else:
                skipped += 1
        return {
            "created": len(created_ids),
            "job_ids": created_ids,
            "skipped": skipped,
            "horizon_days": horizon,
        }

    async def instantiate_series(
        self,
        user_id: int,
        series_id: int,
        publish_at: str,
        *,
        status: Optional[str] = None,
    ) -> dict:
        series = await self.get_series(user_id, series_id)
        if not series:
            raise ValueError("Series not found")
        try:
            pub_at = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid publish_at: {publish_at!r}") from exc
        pub_naive = pub_at.replace(tzinfo=None) if pub_at.tzinfo else pub_at
        job = await self._create_instance_job(
            user_id=user_id,
            series=series,
            publish_at=pub_naive,
            status_override=status,
        )
        if not job:
            raise ValueError("Failed to create job from series")
        return job

    async def expand_brand_series_lazy(
        self, user_id: int, brand_id: int
    ) -> dict[str, Any]:
        """Expand active series whose updated_at is newer than latest linked job."""
        series_list = await self.list_series(user_id, brand_id, active_only=True)
        total_created = 0
        for series in series_list:
            if await self._needs_expand(series["id"], series.get("updated_at")):
                result = await self.expand_series(user_id, series["id"])
                total_created += int(result.get("created") or 0)
        return {"created": total_created, "series": len(series_list)}

    async def _needs_expand(
        self, series_id: int, series_updated_at: Optional[str]
    ) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT MAX(created_at) FROM smm_publish_jobs
                    WHERE series_id = %s
                    """,
                    (series_id,),
                )
                row = await cur.fetchone()
                latest = row[0] if row else None
                if latest is None:
                    return True
                if not series_updated_at:
                    return False
                try:
                    series_ts = datetime.fromisoformat(
                        series_updated_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    return False
                latest_naive = (
                    latest.replace(tzinfo=None) if getattr(latest, "tzinfo", None) else latest
                )
                series_naive = (
                    series_ts.replace(tzinfo=None)
                    if series_ts.tzinfo
                    else series_ts
                )
                return series_naive > latest_naive
        finally:
            await release_db_connection(conn)

    async def _existing_instance_dates(self, series_id: int) -> set[date]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT DISTINCT (publish_at AT TIME ZONE 'UTC')::date
                    FROM smm_publish_jobs
                    WHERE series_id = %s AND publish_at IS NOT NULL
                    """,
                    (series_id,),
                )
                rows = await cur.fetchall()
                out: set[date] = set()
                for r in rows:
                    if r and r[0]:
                        out.add(r[0] if isinstance(r[0], date) else date.fromisoformat(str(r[0])[:10]))
                return out
        finally:
            await release_db_connection(conn)

    async def _cancel_future_instances(self, owner_user_id: int, series_id: int) -> int:
        """Remove unpublished future instances so rebuild can recreate them."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM smm_publish_jobs
                    WHERE series_id = %s
                      AND user_id = %s
                      AND status = ANY(%s)
                      AND (publish_at IS NULL OR publish_at > NOW())
                    """,
                    (series_id, owner_user_id, list(MUTABLE_JOB_STATUSES)),
                )
                return int(cur.rowcount or 0)
        finally:
            await release_db_connection(conn)

    async def _create_instance_job(
        self,
        *,
        user_id: int,
        series: dict[str, Any],
        publish_at: datetime,
        status_override: Optional[str] = None,
    ) -> Optional[dict]:
        targets = series.get("targets") or []
        text = str(series.get("body") or series.get("title") or "Content")
        pub_iso = publish_at.isoformat()
        preferred = status_override or ("scheduled" if targets else "draft")
        try:
            return await smm_service.create_job(
                user_id=user_id,
                brand_id=series["brand_id"],
                text=text,
                media=[],
                targets=targets,
                publish_at=pub_iso,
                adapt=bool(targets),
                status=preferred,
                charge_quota=False,
                series_id=series["id"],
            )
        except Exception as exc:
            logger.info(
                "series %s instantiate as draft after %s: %s",
                series["id"],
                preferred,
                exc,
            )
            if preferred == "draft":
                return None
            try:
                return await smm_service.create_job(
                    user_id=user_id,
                    brand_id=series["brand_id"],
                    text=text,
                    media=[],
                    targets=targets,
                    publish_at=pub_iso,
                    adapt=False,
                    status="draft",
                    charge_quota=False,
                    series_id=series["id"],
                )
            except Exception as inner:
                logger.warning("series instantiate failed: %s", inner)
                return None

    async def _get_template(
        self, user_id: int, template_id: int
    ) -> Optional[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, kind, body, user_id
                    FROM smm_templates
                    WHERE id = %s
                    """,
                    (template_id,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                # Allow brand owner templates when actor is a teammate.
                brand = await smm_service.get_brand(user_id, int(row[1]))
                if not brand:
                    return None
                return {
                    "id": row[0],
                    "brand_id": row[1],
                    "kind": row[2],
                    "body": row[3] or "",
                    "user_id": row[4],
                }
        finally:
            await release_db_connection(conn)


content_series_service = ContentSeriesService()

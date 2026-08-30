"""Content library: brand templates, media packs, UTM/CTA helpers, republish-variant."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from database import get_db_connection, release_db_connection
from exceptions import QuotaExceededError
from services.quota_service import (
    ensure_ai_calls_quota,
    ensure_smm_feature,
    ensure_smm_limit,
    plan_feature,
)
from services.smm_service import compose_brand_voice, smm_service

logger = logging.getLogger(__name__)

TemplateKind = Literal["prompt", "cta", "utm", "post_body"]
TEMPLATE_KINDS = frozenset({"prompt", "cta", "utm", "post_body"})

MAX_TITLE = 255
MAX_BODY = 20000
MAX_CAPTION = 2000
MAX_OBJECT_KEYS = 20
MAX_UTM_PARAMS = 20

TEMPLATE_SELECT = (
    "id, user_id, brand_id, kind, title, body, metadata, created_at, updated_at"
)
MEDIA_PACK_SELECT = (
    "id, user_id, brand_id, title, object_keys, caption, created_at, updated_at"
)


def build_utm_url(base_url: str, params: dict[str, Any] | None = None) -> str:
    """Merge UTM/query params into base URL."""
    url = (base_url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if params:
        for key, val in list(params.items())[:MAX_UTM_PARAMS]:
            k = str(key or "").strip()
            if not k:
                continue
            existing[k] = str(val if val is not None else "").strip()
    query = urlencode(existing)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment)
    )


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


def _sanitize_metadata(raw: Any) -> dict[str, Any]:
    data = _parse_json_field(raw, {})
    if not isinstance(data, dict):
        return {}
    # Keep JSON-serializable shallow dict
    out: dict[str, Any] = {}
    for key, val in list(data.items())[:50]:
        k = str(key)[:80]
        if isinstance(val, (str, int, float, bool)) or val is None:
            out[k] = val
        elif isinstance(val, dict):
            nested: dict[str, Any] = {}
            for nk, nv in list(val.items())[:MAX_UTM_PARAMS]:
                if isinstance(nv, (str, int, float, bool)) or nv is None:
                    nested[str(nk)[:80]] = nv
            out[k] = nested
        elif isinstance(val, list):
            out[k] = [
                str(x)[:200] if not isinstance(x, (int, float, bool)) else x
                for x in val[:20]
            ]
    return out


def _sanitize_object_keys(raw: Any) -> list[str]:
    data = _parse_json_field(raw, [])
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data[:MAX_OBJECT_KEYS]:
        key = str(item or "").strip()[:512]
        if key:
            out.append(key)
    return out


def _row_template(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "kind": r[3],
        "title": r[4],
        "body": r[5] or "",
        "metadata": _parse_json_field(r[6], {}),
        "created_at": _iso_dt(r[7]),
        "updated_at": _iso_dt(r[8]),
    }


def _row_media_pack(r: tuple) -> dict[str, Any]:
    return {
        "id": r[0],
        "user_id": r[1],
        "brand_id": r[2],
        "title": r[3],
        "object_keys": _sanitize_object_keys(r[4]),
        "caption": r[5],
        "created_at": _iso_dt(r[6]),
        "updated_at": _iso_dt(r[7]),
    }


def resolve_template_text(template: dict[str, Any]) -> dict[str, Any]:
    """Compute insertable text + mode for a template."""
    kind = template.get("kind") or "post_body"
    body = str(template.get("body") or "")
    meta = template.get("metadata") if isinstance(template.get("metadata"), dict) else {}

    if kind == "prompt":
        return {
            "kind": kind,
            "mode": "prompt",
            "text": body.strip(),
            "prompt_note": body.strip(),
        }

    if kind == "cta":
        return {
            "kind": kind,
            "mode": "append",
            "text": body.strip(),
            "networks": meta.get("networks") if isinstance(meta.get("networks"), list) else [],
        }

    if kind == "utm":
        base = str(meta.get("base_url") or body or "").strip()
        params = meta.get("params") if isinstance(meta.get("params"), dict) else {}
        url = build_utm_url(base, params)
        label = str(meta.get("label") or "").strip()
        text = f"{label} {url}".strip() if label else url
        return {
            "kind": kind,
            "mode": "append",
            "text": text,
            "url": url,
        }

    # post_body
    return {
        "kind": "post_body",
        "mode": "replace",
        "text": body,
    }


class ContentLibraryService:
    async def _require_brand(self, user_id: int, brand_id: int) -> dict:
        brand = await smm_service.get_brand(user_id, brand_id)
        if not brand:
            raise ValueError("Brand not found")
        return brand

    async def _get_job(self, user_id: int, job_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, brand_id, source_text, media, targets, adapters_result,
                           publish_at, status, created_at, updated_at
                    FROM smm_publish_jobs
                    WHERE id = %s AND user_id = %s
                    """,
                    (job_id, user_id),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                from services.smm_service import _row_job

                return _row_job(row)
        finally:
            await release_db_connection(conn)

    # ---------- Templates ----------

    async def count_templates(self, user_id: int) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM smm_templates WHERE user_id = %s",
                    (user_id,),
                )
                row = await cur.fetchone()
                return int(row[0] if row else 0)
        finally:
            await release_db_connection(conn)

    async def list_templates(
        self,
        user_id: int,
        brand_id: int,
        kind: Optional[str] = None,
    ) -> list[dict]:
        await self._require_brand(user_id, brand_id)
        conditions = ["user_id = %s", "brand_id = %s"]
        params: list[Any] = [user_id, brand_id]
        if kind and kind in TEMPLATE_KINDS:
            conditions.append("kind = %s")
            params.append(kind)
        where = " AND ".join(conditions)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {TEMPLATE_SELECT}
                    FROM smm_templates
                    WHERE {where}
                    ORDER BY kind, title
                    LIMIT 500
                    """,
                    params,
                )
                rows = await cur.fetchall()
                return [_row_template(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def get_template(self, user_id: int, template_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {TEMPLATE_SELECT}
                    FROM smm_templates
                    WHERE id = %s AND user_id = %s
                    """,
                    (template_id, user_id),
                )
                row = await cur.fetchone()
                return _row_template(row) if row else None
        finally:
            await release_db_connection(conn)

    async def create_template(
        self,
        user_id: int,
        brand_id: int,
        kind: str,
        title: str,
        body: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        await self._require_brand(user_id, brand_id)
        if kind not in TEMPLATE_KINDS:
            raise ValueError(f"Invalid kind: {kind}")
        used = await self.count_templates(user_id)
        await ensure_smm_limit(user_id, "max_templates", used, units=1)
        title_clean = (title or "").strip()[:MAX_TITLE]
        if not title_clean:
            raise ValueError("Title is required")
        body_clean = (body or "")[:MAX_BODY]
        meta = _sanitize_metadata(metadata)
        if kind == "utm":
            base = str(meta.get("base_url") or body_clean or "").strip()
            if not base:
                raise ValueError("UTM template requires base_url in metadata or body")
            meta.setdefault("base_url", base)
            if "params" not in meta or not isinstance(meta.get("params"), dict):
                meta["params"] = {}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    INSERT INTO smm_templates (user_id, brand_id, kind, title, body, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING {TEMPLATE_SELECT}
                    """,
                    (
                        user_id,
                        brand_id,
                        kind,
                        title_clean,
                        body_clean,
                        json.dumps(meta, ensure_ascii=False),
                    ),
                )
                row = await cur.fetchone()
                return _row_template(row)
        finally:
            await release_db_connection(conn)

    async def update_template(
        self,
        user_id: int,
        template_id: int,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
        metadata: Optional[dict] = None,
        kind: Optional[str] = None,
    ) -> Optional[dict]:
        tpl = await self.get_template(user_id, template_id)
        if not tpl:
            return None
        new_kind = kind if kind in TEMPLATE_KINDS else tpl["kind"]
        new_title = title.strip()[:MAX_TITLE] if title is not None else tpl["title"]
        if not new_title:
            raise ValueError("Title is required")
        new_body = body[:MAX_BODY] if body is not None else tpl["body"]
        new_meta = _sanitize_metadata(metadata) if metadata is not None else tpl["metadata"]
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_templates
                    SET kind = %s, title = %s, body = %s, metadata = %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING {TEMPLATE_SELECT}
                    """,
                    (
                        new_kind,
                        new_title,
                        new_body,
                        json.dumps(new_meta, ensure_ascii=False),
                        template_id,
                        user_id,
                    ),
                )
                row = await cur.fetchone()
                return _row_template(row) if row else None
        finally:
            await release_db_connection(conn)

    async def delete_template(self, user_id: int, template_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_templates WHERE id = %s AND user_id = %s",
                    (template_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def apply_template(
        self,
        user_id: int,
        template_id: int,
        *,
        job_id: Optional[int] = None,
        current_text: Optional[str] = None,
    ) -> dict[str, Any]:
        tpl = await self.get_template(user_id, template_id)
        if not tpl:
            raise ValueError("Template not found")
        applied = resolve_template_text(tpl)
        job = None
        result_text = applied.get("text") or ""

        if job_id is not None:
            source = await self._get_job(user_id, job_id)
            if not source:
                raise ValueError("Job not found")
            base_text = current_text if current_text is not None else (source.get("source_text") or "")
            mode = applied.get("mode")
            if mode == "replace":
                new_text = result_text
            elif mode == "append":
                new_text = f"{base_text.rstrip()}\n\n{result_text}".strip() if result_text else base_text
            else:
                # prompt: do not mutate job text
                new_text = base_text
            if mode in ("replace", "append") and new_text != base_text:
                job = await smm_service.update_job(user_id, job_id, source_text=new_text)
            else:
                job = source
            result_text = new_text if mode in ("replace", "append") else result_text

        return {
            "template": tpl,
            "applied": applied,
            "text": result_text,
            "job": job,
        }

    # ---------- Media packs ----------

    async def count_media_packs(self, user_id: int) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM smm_media_packs WHERE user_id = %s",
                    (user_id,),
                )
                row = await cur.fetchone()
                return int(row[0] if row else 0)
        finally:
            await release_db_connection(conn)

    async def list_media_packs(self, user_id: int, brand_id: int) -> list[dict]:
        await self._require_brand(user_id, brand_id)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {MEDIA_PACK_SELECT}
                    FROM smm_media_packs
                    WHERE user_id = %s AND brand_id = %s
                    ORDER BY title
                    LIMIT 200
                    """,
                    (user_id, brand_id),
                )
                rows = await cur.fetchall()
                return [_row_media_pack(r) for r in rows]
        finally:
            await release_db_connection(conn)

    async def get_media_pack(self, user_id: int, pack_id: int) -> Optional[dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {MEDIA_PACK_SELECT}
                    FROM smm_media_packs
                    WHERE id = %s AND user_id = %s
                    """,
                    (pack_id, user_id),
                )
                row = await cur.fetchone()
                return _row_media_pack(row) if row else None
        finally:
            await release_db_connection(conn)

    async def create_media_pack(
        self,
        user_id: int,
        brand_id: int,
        title: str,
        object_keys: Optional[list[str]] = None,
        caption: Optional[str] = None,
    ) -> dict:
        await self._require_brand(user_id, brand_id)
        used = await self.count_media_packs(user_id)
        await ensure_smm_limit(user_id, "max_media_packs", used, units=1)
        title_clean = (title or "").strip()[:MAX_TITLE]
        if not title_clean:
            raise ValueError("Title is required")
        keys = _sanitize_object_keys(object_keys)
        cap = (caption or "").strip()[:MAX_CAPTION] or None
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    INSERT INTO smm_media_packs
                        (user_id, brand_id, title, object_keys, caption)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    RETURNING {MEDIA_PACK_SELECT}
                    """,
                    (
                        user_id,
                        brand_id,
                        title_clean,
                        json.dumps(keys, ensure_ascii=False),
                        cap,
                    ),
                )
                row = await cur.fetchone()
                return _row_media_pack(row)
        finally:
            await release_db_connection(conn)

    async def update_media_pack(
        self,
        user_id: int,
        pack_id: int,
        *,
        title: Optional[str] = None,
        object_keys: Optional[list[str]] = None,
        caption: Optional[str] = None,
        clear_caption: bool = False,
    ) -> Optional[dict]:
        pack = await self.get_media_pack(user_id, pack_id)
        if not pack:
            return None
        new_title = title.strip()[:MAX_TITLE] if title is not None else pack["title"]
        if not new_title:
            raise ValueError("Title is required")
        new_keys = (
            _sanitize_object_keys(object_keys)
            if object_keys is not None
            else pack["object_keys"]
        )
        if clear_caption:
            new_cap = None
        elif caption is not None:
            new_cap = caption.strip()[:MAX_CAPTION] or None
        else:
            new_cap = pack.get("caption")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE smm_media_packs
                    SET title = %s, object_keys = %s::jsonb, caption = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING {MEDIA_PACK_SELECT}
                    """,
                    (
                        new_title,
                        json.dumps(new_keys, ensure_ascii=False),
                        new_cap,
                        pack_id,
                        user_id,
                    ),
                )
                row = await cur.fetchone()
                return _row_media_pack(row) if row else None
        finally:
            await release_db_connection(conn)

    async def delete_media_pack(self, user_id: int, pack_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM smm_media_packs WHERE id = %s AND user_id = %s",
                    (pack_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            await release_db_connection(conn)

    async def apply_media_pack(
        self,
        user_id: int,
        pack_id: int,
        *,
        job_id: Optional[int] = None,
        merge: bool = True,
    ) -> dict[str, Any]:
        pack = await self.get_media_pack(user_id, pack_id)
        if not pack:
            raise ValueError("Media pack not found")
        keys = list(pack.get("object_keys") or [])
        caption = pack.get("caption")
        job = None
        if job_id is not None:
            source = await self._get_job(user_id, job_id)
            if not source:
                raise ValueError("Job not found")
            existing = list(source.get("media") or [])
            media = list(dict.fromkeys([*existing, *keys])) if merge else keys
            fields: dict[str, Any] = {"media": media}
            if caption and not (source.get("source_text") or "").strip():
                fields["source_text"] = caption
            job = await smm_service.update_job(user_id, job_id, **fields)
        return {
            "media_pack": pack,
            "media": keys,
            "caption": caption,
            "job": job,
        }

    # ---------- Republish with variation ----------

    async def republish_variant(
        self,
        user_id: int,
        job_id: int,
        *,
        pending_approval: Optional[bool] = None,
        network: Optional[str] = None,
    ) -> dict[str, Any]:
        source = await self._get_job(user_id, job_id)
        if not source:
            raise ValueError("Job not found")

        text = str(source.get("source_text") or "").strip()
        if not text:
            raise ValueError("Source job has no text")

        brand = None
        brand_id = source.get("brand_id")
        if brand_id:
            brand = await smm_service.get_brand(user_id, int(brand_id))
        tone = compose_brand_voice(brand)

        rewritten = text
        ai_used = False
        from services.quota_service import get_user_tariff

        tariff = await get_user_tariff(user_id)
        if plan_feature(tariff, "ai_composer", False):
            try:
                await ensure_ai_calls_quota(user_id, units=1)
                from shared.ai_client import rewrite

                rewritten = await rewrite(text, tone=tone, network=network)
                ai_used = True
            except QuotaExceededError:
                raise
            except Exception as exc:
                logger.warning("republish rewrite fallback: %s", exc)
                rewritten = text

        use_approval = pending_approval
        if use_approval is None:
            try:
                await ensure_smm_feature(user_id, "approval_workflow")
                use_approval = True
            except QuotaExceededError:
                use_approval = False

        status = "pending_approval" if use_approval else "draft"
        media = list(source.get("media") or [])
        targets = list(source.get("targets") or [])

        job = await smm_service.create_job(
            user_id=user_id,
            brand_id=brand_id,
            text=rewritten,
            media=media,
            targets=targets,
            publish_at=None,
            adapt=True,
            status=status,
        )
        return {
            "source_job_id": job_id,
            "job": job,
            "ai_used": ai_used,
            "tone": tone,
        }


content_library_service = ContentLibraryService()

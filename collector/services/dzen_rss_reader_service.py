"""Сбор постов из внешних RSS-лент Дзен (channels_to_read) в dzen_posts."""

import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from database import get_db_connection

logger = logging.getLogger(__name__)

# Namespaces для RSS Дзена / стандартного RSS
NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "media": "http://search.yahoo.com/mrss/",
    "yandex": "http://news.yandex.ru",
}


def _fetch_rss_sync(url: str, timeout: int = 15) -> str:
    """Синхронно загружает RSS по URL. Вызывать из asyncio.to_thread."""
    req = Request(url, headers={"User-Agent": "DzenRssCollector/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_rss_items(xml_text: str) -> list[dict[str, Any]]:
    """Парсит RSS XML и возвращает список item: title, link, pubDate, description/full-text, images."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("RSS parse error: %s", e)
        return items
    channel = root.find("channel")
    if channel is None:
        return items
    for item in channel.findall("item"):
        title_el = item.find("title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        link_el = item.find("link")
        link = (link_el.text or "").strip() if link_el is not None else ""
        pub_el = item.find("pubDate")
        pub_date = None
        if pub_el is not None and pub_el.text:
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(pub_el.text.strip())
            except (ValueError, TypeError):
                pass
        full_text_el = item.find("yandex:full-text", NS) or item.find("full-text", NS)
        if full_text_el is None:
            full_text_el = item.find("content:encoded", NS) or item.find("description")
        post_text = (full_text_el.text or "").strip() if full_text_el is not None else ""
        images = []
        for enc in item.findall("enclosure"):
            url_attr = enc.get("url")
            type_attr = (enc.get("type") or "").lower()
            if url_attr and ("image" in type_attr or type_attr in ("", "image/jpeg", "image/png")):
                images.append(url_attr)
        for content in item.findall("media:content", NS):
            url_attr = content.get("url")
            if url_attr:
                images.append(url_attr)
        items.append({
            "title": title,
            "link": link,
            "pub_date": pub_date,
            "post_text": post_text,
            "images": images,
        })
    return items


class DzenRssReaderService:
    """Сервис вычитки внешних RSS-лент в dzen_posts."""

    def __init__(self) -> None:
        self.last_run_at: datetime | None = None
        self.total_collected: int = 0
        self.last_cycle_collected: int = 0

    async def run_dzen_rss_cycle(self) -> int:
        """Один цикл: для каждого dzen_profile с collect_enabled и channels_to_read загружает RSS и вставляет в dzen_posts."""
        cycle_count = 0
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, channels_to_read
                    FROM dzen_profiles
                    WHERE collect_enabled = TRUE
                      AND COALESCE(collect_source, 'rss') IN ('rss', 'both')
                      AND channels_to_read IS NOT NULL
                      AND channels_to_read != '[]'
                      AND jsonb_array_length(channels_to_read) > 0
                    """
                )
                rows = await cur.fetchall()
        for (user_id, channels_to_read_raw) in rows:
            try:
                if isinstance(channels_to_read_raw, str):
                    channels_to_read = json.loads(channels_to_read_raw)
                else:
                    channels_to_read = channels_to_read_raw or []
            except (json.JSONDecodeError, TypeError):
                channels_to_read = []
            for rss_url in channels_to_read:
                if not isinstance(rss_url, str) or not rss_url.strip():
                    continue
                rss_url = rss_url.strip()
                try:
                    xml_text = await asyncio.to_thread(_fetch_rss_sync, rss_url)
                except (URLError, HTTPError, OSError) as e:
                    logger.warning("Dzen RSS fetch %s: %s", rss_url, e)
                    continue
                items = _parse_rss_items(xml_text)
                for it in items:
                    try:
                        n = await self._insert_item(user_id=user_id, item=it)
                        cycle_count += n
                    except Exception as e:
                        logger.exception("Dzen RSS insert for user %s: %s", user_id, e)
        self.last_run_at = datetime.now(timezone.utc)
        self.last_cycle_collected = cycle_count
        self.total_collected += cycle_count
        if cycle_count > 0:
            logger.info("Dzen RSS reader: %d posts collected", cycle_count)
        return cycle_count

    async def _insert_item(
        self,
        user_id: int,
        item: dict[str, Any],
    ) -> int:
        """Вставляет один item в dzen_posts если такого url ещё нет. Возвращает 1 если вставлен, 0 иначе."""
        link = (item.get("link") or "").strip()
        if not link:
            return 0
        async with get_db_connection() as conn_inner:
            cur = await conn_inner.cursor()
            try:
                await cur.execute(
                    "SELECT 1 FROM dzen_posts WHERE user_id = %s AND url = %s LIMIT 1",
                    (user_id, link),
                )
                if await cur.fetchone():
                    return 0
                post_date = item.get("pub_date")
                images_json = json.dumps(item.get("images") or [], ensure_ascii=False)
                await cur.execute(
                    """
                    INSERT INTO dzen_posts (
                        user_id, url, title, post_date, post_text, images,
                        status, post_type, to_dzen
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'collected', 'dzen_rss', TRUE)
                    """,
                    (
                        user_id,
                        link,
                        (item.get("title") or "")[:500],
                        post_date,
                        (item.get("post_text") or "")[:150000],
                        images_json,
                    ),
                )
                return 1
            finally:
                cur.close()


dzen_rss_reader_service = DzenRssReaderService()

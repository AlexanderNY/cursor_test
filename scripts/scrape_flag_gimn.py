"""Скачивает флаги и метаданные с https://flag-gimn.ru/flags/ в CSV + PNG."""

from __future__ import annotations

import csv
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PAGE_URL = "https://flag-gimn.ru/flags/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
COOKIE = "beget=begetok"

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "flag-gimn"
IMAGES_DIR = OUT_DIR / "images"
CSV_PATH = OUT_DIR / "flags.csv"


class FlagsGridParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_ul = False
        self.in_li = False
        self.in_a = False
        self.in_img = False
        self.in_country_span = False
        self.in_info_p = False
        self.skip_download_p = False
        self.current: dict[str, str] | None = None
        self.items: list[dict[str, str]] = []
        self._info_field: str | None = None
        self._text_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "ul" and attr.get("class") == "flags-grid-loop":
            self.in_ul = True
            return
        if not self.in_ul:
            return
        if tag == "li" and "flag-grid-block" in (attr.get("class") or ""):
            self.in_li = True
            self.current = {"id": attr.get("id", "")}
            return
        if not self.in_li or not self.current:
            return
        if tag == "a":
            self.in_a = True
            return
        if tag == "img" and self.in_a:
            self.in_img = True
            src = attr.get("src") or ""
            if src:
                self.current["image_url"] = src
            return
        if tag == "span" and self.in_a and not self.in_info_p:
            self.in_country_span = True
            self._text_buf = []
            return
        if tag == "p" and self.in_a and "flag-grid-block-info" in (attr.get("class") or ""):
            if "flag-grid-block-dwnld" in (attr.get("class") or ""):
                self.skip_download_p = True
                return
            self.in_info_p = True
            self._text_buf = []
            inner_span = re.search(r"<span>([^<]+)</span>", self.get_starttag_text() or "")
            return
        if tag == "span" and self.in_info_p:
            label = (attr.get("class") or "") + " " + ""
            _ = label
            self._text_buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "ul" and self.in_ul:
            self.in_ul = False
            return
        if tag == "li" and self.in_li:
            if self.current and self.current.get("country"):
                self.items.append(self.current)
            self.in_li = False
            self.in_a = False
            self.current = None
            return
        if tag == "a" and self.in_a:
            self.in_a = False
            return
        if tag == "img" and self.in_img:
            self.in_img = False
            return
        if tag == "span" and self.in_country_span:
            self.in_country_span = False
            if self.current is not None:
                self.current["country"] = self._normalize("".join(self._text_buf))
            return
        if tag == "p" and self.in_info_p:
            text = self._normalize("".join(self._text_buf))
            if self.current is not None and text:
                if text.startswith("Столица:"):
                    self.current["capital"] = text.replace("Столица:", "", 1).strip()
                elif text.startswith("Население:"):
                    self.current["population"] = text.replace("Население:", "", 1).strip()
                elif text.startswith("Валюта:"):
                    self.current["currency"] = text.replace("Валюта:", "", 1).strip()
            self.in_info_p = False
            self._text_buf = []
            return
        if tag == "p" and self.skip_download_p:
            self.skip_download_p = False

    def handle_data(self, data: str) -> None:
        if self.in_country_span or self.in_info_p:
            self._text_buf.append(data)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Cookie": COOKIE})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_flags(html: str) -> list[dict[str, str]]:
    """Парсинг через regex — надёжнее для табов/переносов в HTML."""
    ul_match = re.search(
        r'<ul class="flags-grid-loop">(.*?)</ul>',
        html,
        flags=re.DOTALL,
    )
    if not ul_match:
        raise RuntimeError("flags-grid-loop not found in page HTML")
    block = ul_match.group(1)
    items: list[dict[str, str]] = []
    for li_html in re.findall(
        r'<li id="(flag-\d+)" class="flag-grid-block">(.*?)</li>',
        block,
        flags=re.DOTALL,
    ):
        flag_id, inner = li_html
        img = re.search(r'<img[^>]+src="([^"]+)"', inner)
        country = re.search(r'<img[^>]*>\s*<span>([^<]+)</span>', inner, re.DOTALL)
        if not img or not country:
            continue
        capital = _field(inner, "Столица:")
        population = _field(inner, "Население:")
        currency = _field(inner, "Валюта:")
        items.append(
            {
                "id": flag_id,
                "country": country.group(1).strip(),
                "capital": capital,
                "population": population,
                "currency": currency,
                "image_url": img.group(1).strip(),
            }
        )
    return items


def _field(inner: str, label: str) -> str:
    m = re.search(
        rf'<p class="flag-grid-block-info[^"]*">\s*<span>{re.escape(label)}</span>\s*([^<]+)',
        inner,
        flags=re.DOTALL,
    )
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def safe_filename(url: str, flag_id: str) -> str:
    name = Path(url.split("?")[0]).name or f"{flag_id}.png"
    name = re.sub(r"[^\w.\-]", "_", name)
    return name


def download_file(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    req = Request(url, headers={"User-Agent": USER_AGENT, "Cookie": COOKIE})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {PAGE_URL} ...")
    html = fetch_html(PAGE_URL)
    items = parse_flags(html)
    print(f"Parsed {len(items)} countries")

    rows: list[dict[str, str]] = []
    used_names: dict[str, int] = {}

    for i, item in enumerate(items, start=1):
        base = safe_filename(item["image_url"], item["id"])
        if base in used_names:
            stem = Path(base).stem
            ext = Path(base).suffix
            base = f"{stem}_{item['id']}{ext}"
        used_names[base] = 1

        dest = IMAGES_DIR / base
        try:
            download_file(item["image_url"], dest)
        except (HTTPError, URLError, TimeoutError) as e:
            print(f"  skip image {base}: {e}", file=sys.stderr)
            continue

        rows.append(
            {
                "страна": item["country"],
                "столица": item["capital"],
                "население": item["population"],
                "валюта": item["currency"],
                "флаг": base,
            }
        )
        if i % 25 == 0:
            print(f"  downloaded {i}/{len(items)}")
            time.sleep(0.2)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["страна", "столица", "население", "валюта", "флаг"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV: {CSV_PATH}")
    print(f"Images: {IMAGES_DIR} ({len(rows)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

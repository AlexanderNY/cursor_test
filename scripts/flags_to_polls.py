"""Загрузка флагов в медиатеку tg-game и сборка CSV для импорта Polls."""

from __future__ import annotations

import csv
import json
import random
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
FLAGS_CSV = ROOT / "data" / "flag-gimn" / "flags.csv"
IMAGES_DIR = ROOT / "data" / "flag-gimn" / "images"
MEDIA_MAP_PATH = ROOT / "data" / "flag-gimn" / "media_urls.json"
POLLS_CSV_PATH = ROOT / "data" / "flag-gimn" / "polls_flags_import.csv"

API_BASE = "http://localhost:8015"
ADMIN_TOKEN = "122"
PROMPT_TEXT = "Угадайте страну по флагу"
RANDOM_SEED = 42


def load_countries() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with FLAGS_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            flag_file = (row.get("флаг") or "").strip()
            country = (row.get("страна") or "").strip()
            if not flag_file or not country:
                continue
            rows.append(
                {
                    "country": country,
                    "capital": (row.get("столица") or "").strip(),
                    "population": (row.get("население") or "").strip(),
                    "currency": (row.get("валюта") or "").strip(),
                    "flag_file": flag_file,
                }
            )
    return rows


def fetch_existing_media(client: httpx.Client) -> dict[str, str]:
    """original_filename -> public_url"""
    resp = client.get("/tg/game/admin/media")
    resp.raise_for_status()
    mapping: dict[str, str] = {}
    for item in resp.json():
        orig = (item.get("original_filename") or "").strip()
        title = (item.get("title") or "").strip()
        url = (item.get("public_url") or "").strip()
        if orig and url:
            mapping[orig] = url
        if title.startswith("Флаг ") and url:
            # fallback by country title
            mapping.setdefault(title.replace("Флаг ", "", 1), url)
    return mapping


def upload_flag(
    client: httpx.Client,
    *,
    image_path: Path,
    country: str,
    capital: str,
) -> str:
    with image_path.open("rb") as fh:
        resp = client.post(
            "/tg/game/admin/media",
            files={"file": (image_path.name, fh, "image/png")},
            data={
                "title": f"Флаг {country}",
                "description": f"Столица: {capital}" if capital else "",
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return str(data["public_url"])


def ensure_media_urls(client: httpx.Client, countries: list[dict[str, str]]) -> dict[str, str]:
    if MEDIA_MAP_PATH.exists():
        cached = json.loads(MEDIA_MAP_PATH.read_text(encoding="utf-8"))
        if isinstance(cached, dict) and len(cached) >= len(countries):
            return {k: str(v) for k, v in cached.items()}

    existing = fetch_existing_media(client)
    result: dict[str, str] = {}

    for i, row in enumerate(countries, start=1):
        flag_file = row["flag_file"]
        image_path = IMAGES_DIR / flag_file
        if not image_path.exists():
            print(f"  missing image: {image_path}", file=sys.stderr)
            continue

        if flag_file in existing:
            result[flag_file] = existing[flag_file]
            continue

        if flag_file in result:
            continue

        print(f"  upload {i}/{len(countries)}: {flag_file} ({row['country']})")
        try:
            url = upload_flag(
                client,
                image_path=image_path,
                country=row["country"],
                capital=row["capital"],
            )
            result[flag_file] = url
            existing[flag_file] = url
        except httpx.HTTPError as e:
            print(f"  upload failed {flag_file}: {e}", file=sys.stderr)
        time.sleep(0.05)

    MEDIA_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEDIA_MAP_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def build_polls_csv(countries: list[dict[str, str]], media_urls: dict[str, str]) -> int:
    all_names = [c["country"] for c in countries]
    rng = random.Random(RANDOM_SEED)
    rows_out: list[list[str]] = []

    for row in countries:
        flag_file = row["flag_file"]
        correct_name = row["country"]
        public_url = media_urls.get(flag_file, "")
        if not public_url:
            continue

        wrong_pool = [n for n in all_names if n != correct_name]
        if len(wrong_pool) < 5:
            continue
        distractors = rng.sample(wrong_pool, 5)
        options = distractors + [correct_name]
        rng.shuffle(options)
        correct_index = options.index(correct_name) + 1

        rows_out.append(
            [
                PROMPT_TEXT,
                options[0],
                options[1],
                options[2],
                options[3],
                options[4],
                options[5],
                str(correct_index),
                public_url,
            ]
        )

    with POLLS_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "prompt_text",
                "option1",
                "option2",
                "option3",
                "option4",
                "option5",
                "option6",
                "correct",
                "image_url",
            ]
        )
        writer.writerows(rows_out)

    return len(rows_out)


def main() -> int:
    countries = load_countries()
    print(f"Loaded {len(countries)} countries from {FLAGS_CSV}")

    headers = {"X-Game-Admin-Token": ADMIN_TOKEN}
    with httpx.Client(base_url=API_BASE, headers=headers, timeout=120.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        print("Uploading flags to media library...")
        media_urls = ensure_media_urls(client, countries)
        print(f"Media URLs mapped: {len(media_urls)}")

    count = build_polls_csv(countries, media_urls)
    print(f"Polls CSV: {POLLS_CSV_PATH} ({count} questions)")
    return 0 if count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

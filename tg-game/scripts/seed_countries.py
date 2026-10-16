"""
Загрузка справочника стран: факты из data/countries.json, флаги (flagcdn),
карты мира с подсветкой (Natural Earth 110m + Pillow), upsert в Postgres и S3.

Запуск из каталога tg-game (нужны DATABASE_URL и S3_* как у сервиса):

  python scripts/seed_countries.py
  python scripts/seed_countries.py --facts-only
  python scripts/seed_countries.py --skip-maps
  python scripts/seed_countries.py --limit 5

Не запускать против production.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import logging
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = ROOT / "data"
COUNTRIES_JSON = DATA_DIR / "countries.json"
NE_GEOJSON = DATA_DIR / "ne_110m_admin_0_countries.geojson"
NE_GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)
FLAG_URL = "https://flagcdn.com/w320/{iso2}.png"

logger = logging.getLogger("seed_countries")


def _require_db_env() -> None:
    from config import settings

    if not (settings.DATABASE_URL or "").strip():
        raise SystemExit("Не задан DATABASE_URL")


def _require_s3_env() -> None:
    from config import settings

    missing: list[str] = []
    if not (settings.S3_ENDPOINT_URL or "").strip():
        missing.append("S3_ENDPOINT_URL")
    if not (settings.S3_BUCKET or "").strip():
        missing.append("S3_BUCKET")
    if not (settings.S3_ACCESS_KEY or "").strip():
        missing.append("S3_ACCESS_KEY")
    if not (settings.S3_SECRET_KEY or "").strip():
        missing.append("S3_SECRET_KEY")
    if missing:
        raise SystemExit(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + ". Скопируйте .env и заполните секреты (как у tg-game)."
        )


def load_countries_facts() -> list[dict]:
    if not COUNTRIES_JSON.is_file():
        raise SystemExit(
            f"Нет файла {COUNTRIES_JSON}. "
            "Соберите факты скриптом scripts/build_countries_json.py"
        )
    data = json.loads(COUNTRIES_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit("countries.json пуст или повреждён")
    return data


def ensure_natural_earth_geojson(client: httpx.Client) -> Path:
    if NE_GEOJSON.is_file() and NE_GEOJSON.stat().st_size > 10_000:
        return NE_GEOJSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading Natural Earth 110m countries geojson…")
    resp = client.get(NE_GEOJSON_URL)
    resp.raise_for_status()
    NE_GEOJSON.write_bytes(resp.content)
    logger.info("Saved %s", NE_GEOJSON)
    return NE_GEOJSON


def _feature_iso2(props: dict) -> str | None:
    for key in ("ISO_A2", "ISO_A2_EH", "WB_A2"):
        value = str(props.get(key) or "").strip().upper()
        if value and value not in {"-99", "-1", "NONE", "NULL"}:
            return value
    return None


def _lonlat_to_xy(
    lon: float,
    lat: float,
    *,
    width: int,
    height: int,
) -> tuple[int, int]:
    x = int((lon + 180.0) / 360.0 * width)
    y = int((90.0 - lat) / 180.0 * height)
    return x, y


def _iter_polygons(geometry: dict):
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if gtype == "Polygon":
        yield coords
    elif gtype == "MultiPolygon":
        yield from coords


def _draw_ring(
    draw,
    ring: list,
    *,
    width: int,
    height: int,
    fill,
) -> None:
    if len(ring) < 3:
        return
    points = [
        _lonlat_to_xy(float(lon), float(lat), width=width, height=height)
        for lon, lat, *_rest in ring
    ]
    draw.polygon(points, fill=fill)


def render_country_map_png(
    geojson: dict,
    iso2: str,
    *,
    width: int = 960,
    height: int = 480,
) -> bytes | None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), (230, 240, 250))
    draw = ImageDraw.Draw(img)
    land = (180, 180, 180)
    highlight = (220, 50, 50)
    outline = (120, 120, 120)

    features = geojson.get("features") or []
    target = iso2.upper()

    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue
        for polygon in _iter_polygons(geom):
            exterior = polygon[0] if polygon else []
            _draw_ring(draw, exterior, width=width, height=height, fill=land)

    found = False
    for feat in features:
        props = feat.get("properties") or {}
        code = _feature_iso2(props)
        if code != target:
            continue
        found = True
        geom = feat.get("geometry")
        if not geom:
            continue
        for polygon in _iter_polygons(geom):
            exterior = polygon[0] if polygon else []
            _draw_ring(draw, exterior, width=width, height=height, fill=highlight)
            if len(exterior) >= 2:
                pts = [
                    _lonlat_to_xy(
                        float(lon), float(lat), width=width, height=height
                    )
                    for lon, lat, *_rest in exterior
                ]
                draw.line(pts + [pts[0]], fill=outline, width=1)

    if not found:
        logger.warning("No Natural Earth geometry for %s", iso2)
        return None

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


async def upload_png(body: bytes, original_filename: str) -> str:
    from services.media_storage import upload_media_file

    _name, _key, _ctype, public_url = await upload_media_file(
        body=body,
        original_filename=original_filename,
    )
    return public_url


async def seed(
    *,
    limit: int | None,
    skip_maps: bool,
    skip_flags: bool,
    facts_only: bool,
) -> None:
    from database import close_db, init_db
    from game_schema import GAME_TABLE_DDL
    from services.game_repository import game_repository

    await init_db(GAME_TABLE_DDL)
    facts = load_countries_facts()
    if limit is not None:
        facts = facts[:limit]

    geojson = None
    client = httpx.Client(timeout=60.0, follow_redirects=True)
    ok = 0
    try:
        if not skip_maps and not facts_only:
            ensure_natural_earth_geojson(client)
            geojson = json.loads(NE_GEOJSON.read_text(encoding="utf-8"))

        for idx, row in enumerate(facts, start=1):
            iso2 = str(row["iso2"]).upper()
            logger.info("[%s/%s] %s %s", idx, len(facts), iso2, row.get("name_ru"))

            flag_url = None
            map_url = None

            if not facts_only and not skip_flags:
                flag_resp = client.get(FLAG_URL.format(iso2=iso2.lower()))
                if flag_resp.status_code == 200 and flag_resp.content:
                    flag_url = await upload_png(
                        flag_resp.content, f"flag_{iso2.lower()}.png"
                    )
                else:
                    logger.warning(
                        "Flag missing for %s (%s)", iso2, flag_resp.status_code
                    )

            if not facts_only and not skip_maps and geojson is not None:
                png = render_country_map_png(geojson, iso2)
                if png:
                    map_url = await upload_png(png, f"map_{iso2.lower()}.png")

            await game_repository.upsert_country(
                iso2=iso2,
                name_ru=str(row.get("name_ru") or iso2),
                capital_ru=str(row.get("capital_ru") or ""),
                area_km2=(
                    float(row["area_km2"])
                    if row.get("area_km2") is not None
                    else None
                ),
                population=(
                    int(row["population"])
                    if row.get("population") is not None
                    else None
                ),
                flag_image_url=flag_url,
                map_image_url=map_url,
                is_active=True,
            )
            ok += 1
    finally:
        client.close()
        await close_db()

    logger.info("Done. Upserted %s countries.", ok)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Seed game_countries")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-maps", action="store_true")
    parser.add_argument("--skip-flags", action="store_true")
    parser.add_argument(
        "--facts-only",
        action="store_true",
        help="Только факты в БД без картинок (не требует S3)",
    )
    args = parser.parse_args()

    _require_db_env()
    if not args.facts_only and not (args.skip_flags and args.skip_maps):
        _require_s3_env()

    if not args.skip_maps and not args.facts_only:
        try:
            import PIL  # noqa: F401
        except ImportError as exc:
            raise SystemExit(
                "Для карт нужен Pillow: pip install Pillow"
            ) from exc

    asyncio.run(
        seed(
            limit=args.limit,
            skip_maps=args.skip_maps,
            skip_flags=args.skip_flags,
            facts_only=args.facts_only,
        )
    )


if __name__ == "__main__":
    main()

"""Одноразовый сбор tg-game/data/countries.json (без Wikidata — 403 с этой среды)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "countries.json"

WORLD_URL = (
    "https://raw.githubusercontent.com/mledoze/countries/master/dist/countries.json"
)
CSC_URL = (
    "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database"
    "/master/json/countries.json"
)


def main() -> None:
    client = httpx.Client(timeout=120.0, follow_redirects=True)
    world = client.get(WORLD_URL).json()
    csc = client.get(CSC_URL).json()
    csc_by_iso = {
        str(row.get("iso2") or "").upper(): row
        for row in csc
        if row.get("iso2")
    }

    countries: list[dict] = []
    for item in world:
        iso2 = str(item.get("cca2") or "").upper()
        if len(iso2) != 2:
            continue
        if not item.get("independent") and not item.get("unMember"):
            continue

        rus = (item.get("translations") or {}).get("rus") or {}
        name_ru = rus.get("common") or (item.get("name") or {}).get("common") or iso2
        caps = item.get("capital") or []
        capital_en = str(caps[0]) if caps else ""
        extra = csc_by_iso.get(iso2, {})
        capital_ru = capital_en or str(extra.get("capital") or "")
        area_km2 = item.get("area")
        if area_km2 is None and extra.get("area_sq_km") not in (None, ""):
            try:
                area_km2 = float(extra["area_sq_km"])
            except (TypeError, ValueError):
                area_km2 = None
        population = extra.get("population")
        if population is not None:
            try:
                population = int(population)
            except (TypeError, ValueError):
                population = None

        countries.append(
            {
                "iso2": iso2,
                "name_ru": name_ru,
                "capital_ru": capital_ru,
                "area_km2": area_km2,
                "population": population,
            }
        )

    countries.sort(key=lambda c: c["name_ru"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(countries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(countries)} countries to {OUT}")


if __name__ == "__main__":
    main()

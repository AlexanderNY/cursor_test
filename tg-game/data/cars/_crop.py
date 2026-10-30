"""Один прогон: кроп детали и уменьшенный общий вид. Не часть сервиса."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
FULL = ROOT / "full"
DETAIL = ROOT / "detail"

# Доли кадра: left, top, right, bottom. Кроп без эмблемы, чтобы ответ не читался с бейджа.
CROPS: dict[str, tuple[float, float, float, float]] = {
    "bmw-e46": (0.20, 0.50, 0.46, 0.70),
    "audi-a4-b6": (0.16, 0.54, 0.40, 0.74),
    "vw-golf-4": (0.00, 0.50, 0.16, 0.68),
    "toyota-camry-xv40": (0.50, 0.50, 0.72, 0.68),
    "volvo-240": (0.55, 0.48, 0.78, 0.66),
    "mazda-mx5-na": (0.26, 0.40, 0.50, 0.60),
    "porsche-911-996": (0.24, 0.48, 0.48, 0.70),
    "ford-mustang-s197": (0.20, 0.46, 0.40, 0.66),
    "mini-r50": (0.46, 0.46, 0.70, 0.70),
    "skoda-octavia-1": (0.36, 0.52, 0.58, 0.74),
    "toyota-land-cruiser-100": (0.38, 0.42, 0.56, 0.58),
    "lada-niva-travel": (0.26, 0.46, 0.50, 0.64),
}

# Область номера, если он читается на исходнике.
PLATES: dict[str, tuple[float, float, float, float]] = {
    "toyota-camry-xv40": (0.70, 0.60, 0.93, 0.72),
    "toyota-land-cruiser-100": (0.10, 0.58, 0.30, 0.70),
}

FILES = {
    "bmw-e46": "BMW E46 front 20070520.jpg",
    "audi-a4-b6": "Audi A4 B6 front 20070326.jpg",
    "vw-golf-4": "1998 Volkswagen Golf S 1.4 (Front).jpg",
    "toyota-camry-xv40": "Toyota Camry XV40 LE Black Onyx front right.jpg",
    "volvo-240": "1988 Volvo 240 DL sedan, front right, 05-02-2022.jpg",
    "mazda-mx5-na": "1990 Mazda MX-5 Miata, front left, 06-08-2024.jpg",
    "porsche-911-996": "2003 Porsche 911 Carrera 4S coupe, front left, 06-08-2024.jpg",
    "ford-mustang-s197": "Ford MUSTANG V8 GT Coupé Premium (S197) front.JPG",
    "mini-r50": "BMW MINI COOPER (R50) front.JPG",
    "skoda-octavia-1": "Skoda Octavia front 20071007.jpg",
    "toyota-land-cruiser-100": "2001 Toyota Land Cruiser 100 4.2TD VX in White, front left.jpg",
    "lada-niva-travel": "2022 Lada Niva Travel 21230 light brown front.jpg",
}


def _box(width: int, height: int, frac: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    left, top, right, bottom = frac
    return (
        int(width * left),
        int(height * top),
        int(width * right),
        int(height * bottom),
    )


def _cover_plate(image: Image.Image, frac: tuple[float, float, float, float]) -> None:
    box = _box(image.width, image.height, frac)
    plate = image.crop(box).filter(ImageFilter.GaussianBlur(radius=18))
    image.paste(plate, box)


def _limit_width(image: Image.Image, max_width: int) -> Image.Image:
    if image.width <= max_width:
        return image
    height = int(image.height * max_width / image.width)
    return image.resize((max_width, height), Image.Resampling.LANCZOS)


def main() -> None:
    FULL.mkdir(parents=True, exist_ok=True)
    DETAIL.mkdir(parents=True, exist_ok=True)
    report = []
    for slug, filename in FILES.items():
        src = SOURCE / filename
        if not src.is_file():
            raise SystemExit(f"нет файла {src}")
        with Image.open(src) as raw:
            image = raw.convert("RGB")
            if slug in PLATES:
                _cover_plate(image, PLATES[slug])
            full = _limit_width(image, 1200)
            full.save(FULL / f"{slug}.jpg", quality=86, optimize=True)
            crop = image.crop(_box(image.width, image.height, CROPS[slug]))
            crop = _limit_width(crop, 900)
            crop.save(DETAIL / f"{slug}.jpg", quality=86, optimize=True)
            report.append(
                {
                    "slug": slug,
                    "source_px": [image.width, image.height],
                    "detail_px": [crop.width, crop.height],
                }
            )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

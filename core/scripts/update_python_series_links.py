"""Mark SERIES.md bodies as linking to py*.md files."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERIES = ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn" / "python" / "SERIES.md"
DIR = SERIES.parent


def main() -> None:
    slug_to_file: dict[str, str] = {}
    for path in DIR.glob("py*.md"):
        match = re.search(r"^slug:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
        if match:
            slug_to_file[match.group(1)] = path.name

    text = SERIES.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(### PY\d+ · `([^`]+)`[\s\S]*?\*\*Тело:\*\* )TBD"
    )

    def replace(match: re.Match[str]) -> str:
        slug = match.group(2)
        filename = slug_to_file.get(slug)
        if not filename:
            return match.group(0)
        return f"{match.group(1)}[`{filename}`]({filename})"

    new_text, count = pattern.subn(replace, text)
    new_text = new_text.replace(
        "**Пилоты с полным текстом:** PY01, PY02, PY10, PY15, PY17 (файлы `py01-….md` … рядом; уже в `learn_seed.json`).",
        "**Все 24 выпуска** имеют полный текст (`py01-….md` … `py24-….md`) и залиты в `learn_seed.json` / `episodes.ts`.",
    )
    old_next = (
        "## Следующий этап\n\n"
        "1. Дописать оставшиеся `.md` по шаблону (после пилотов PY01, PY02, PY10, PY15, PY17).\n"
        "2. Добавить файлы в `core/scripts/import_python_learn_pilots.py` и перегнать seed.\n"
        "3. `python core/scripts/generate_learn_episodes_ts.py`."
    )
    new_next = (
        "## Обслуживание\n\n"
        "```bash\n"
        "python core/scripts/import_python_learn_pilots.py\n"
        "python core/scripts/generate_learn_episodes_ts.py\n"
        "```\n\n"
        "Скрипт подхватывает все `py*.md` в этой папке."
    )
    if old_next in new_text:
        new_text = new_text.replace(old_next, new_next)
    SERIES.write_text(new_text, encoding="utf-8")
    left = new_text.count("**Тело:** TBD")
    print(f"replacements={count} TBD_left={left}")


if __name__ == "__main__":
    main()

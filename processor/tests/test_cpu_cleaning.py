from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.text_cleaner import apply_cpu_cleaning


def test_apply_cpu_cleaning_html_and_emoji():
    text, images = apply_cpu_cleaning(
        "<p>Hello 🔥</p>",
        ["http://img"],
        {"remove_emojis": True, "remove_images": True, "clean_html": True},
    )
    assert "<p>" not in text
    assert "🔥" not in text
    assert images == []

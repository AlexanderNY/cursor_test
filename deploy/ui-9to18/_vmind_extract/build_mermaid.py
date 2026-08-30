import json
import pathlib
import re

base = pathlib.Path(__file__).resolve().parent
tree = json.loads((base / "interview_prep_tree.json").read_text(encoding="utf-8"))


def clean(text: str, limit: int = 60) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace('"', "'")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text or "—"


def emit_mindmap(node, depth=0, max_depth=2, lines=None):
    if lines is None:
        lines = []
    indent = "  " * depth
    title = clean(node["title"], 70 if depth < 2 else 50)
    if depth == 0:
        lines.append(f"root(({title}))")
    else:
        lines.append(f"{indent}{title}")
    if depth < max_depth:
        for child in node.get("children") or []:
            emit_mindmap(child, depth + 1, max_depth, lines)
    return lines


# Overview: 2 levels
overview = ["mindmap"] + emit_mindmap(tree, 0, 2)
(base / "interview_prep_overview.mmd").write_text("\n".join(overview) + "\n", encoding="utf-8")

# Per-section deep maps (depth 4) for each top branch
sections_dir = base / "sections"
sections_dir.mkdir(exist_ok=True)
for i, child in enumerate(tree.get("children") or [], 1):
    section_root = {"title": child["title"], "children": child.get("children") or []}
    lines = ["mindmap"] + emit_mindmap(section_root, 0, 4)
    slug = re.sub(r"[^\w\-]+", "_", child["title"], flags=re.U)[:40].strip("_") or f"section_{i}"
    path = sections_dir / f"{i:02d}_{slug}.mmd"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("overview nodes approx", len(overview) - 1)
print("sections", len(list(sections_dir.glob("*.mmd"))))
print(overview[:40])

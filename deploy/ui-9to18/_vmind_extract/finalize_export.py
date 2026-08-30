import json
import pathlib
import re
import shutil

base = pathlib.Path(__file__).resolve().parent
out_dir = base.parent / "interview-prep"
out_dir.mkdir(exist_ok=True)

tree = json.loads((base / "interview_prep_tree.json").read_text(encoding="utf-8"))


def clean(text: str, limit: int = 55) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace('"', "'")
    # mermaid mindmap is fragile with punctuation
    text = re.sub(r"[()\[\]{}]", "", text)
    text = text.replace(":", " -")
    text = text.replace("/", "-")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text or "—"


def emit_mindmap(node, depth=0, max_depth=2, lines=None):
    if lines is None:
        lines = []
    indent = "  " * depth
    title = clean(node["title"], 70 if depth < 2 else 48)
    if depth == 0:
        lines.append(f"root(({title}))")
    else:
        lines.append(f"{indent}{title}")
    if depth < max_depth:
        for child in node.get("children") or []:
            emit_mindmap(child, depth + 1, max_depth, lines)
    return lines


overview_lines = ["mindmap"] + emit_mindmap(tree, 0, 2)
overview_text = "\n".join(overview_lines) + "\n"
(out_dir / "overview.mmd").write_text(overview_text, encoding="utf-8")

# full markdown outline
shutil.copy2(base / "interview_prep_outline.md", out_dir / "подготовка-к-собеседованию.md")
shutil.copy2(base / "interview_prep_tree.json", out_dir / "tree.json")

# also write mermaid for create_diagram to a simple ascii-safe path
(out_dir / "overview.mmd").write_text(overview_text, encoding="utf-8")
print(overview_text)
print("---")
print("out_dir", out_dir)
print("lines", len(overview_lines))

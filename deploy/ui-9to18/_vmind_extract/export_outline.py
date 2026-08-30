import json
import pathlib
import re
from html import unescape

base = pathlib.Path(__file__).resolve().parent
data = json.loads((base / "content.json").read_text(encoding="utf-8"))
root = data["sheets"][0]["root"]


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", " / ", text).strip()
    return text


def node_title(node: dict) -> str:
    d = node.get("data") if isinstance(node.get("data"), dict) else node
    for key in ("text", "title", "topic", "name", "html", "content"):
        val = d.get(key)
        if isinstance(val, str) and val.strip():
            return strip_html(val)
    return "Без названия"


def children_of(node: dict) -> list:
    kids = node.get("children")
    return kids if isinstance(kids, list) else []


def walk(node, depth=0, counter=None):
    if counter is not None:
        counter[0] += 1
    title = node_title(node)
    yield depth, title
    for child in children_of(node):
        yield from walk(child, depth + 1, counter)


counter = [0]
lines = []
for depth, title in walk(root, 0, counter):
    # markdown heading for top 2 levels, bullets deeper
    safe = title.replace("\n", " ").strip()
    if not safe:
        safe = "—"
    if depth == 0:
        lines.append(f"# {safe}")
        lines.append("")
    elif depth == 1:
        lines.append(f"## {safe}")
        lines.append("")
    elif depth == 2:
        lines.append(f"### {safe}")
        lines.append("")
    else:
        indent = "  " * (depth - 3)
        lines.append(f"{indent}- {safe}")

md_path = base / "interview_prep_outline.md"
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

# also JSON tree for reuse
def to_tree(node):
    return {
        "title": node_title(node),
        "children": [to_tree(c) for c in children_of(node)],
    }


tree = to_tree(root)
(base / "interview_prep_tree.json").write_text(
    json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"nodes={counter[0]}")
print(f"md_lines={len(lines)}")
print(f"top_children={len(children_of(root))}")
print("written", md_path.name)

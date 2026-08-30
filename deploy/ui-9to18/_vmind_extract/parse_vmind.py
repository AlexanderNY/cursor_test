import json
import pathlib
import re
from html import unescape

p = pathlib.Path(__file__).with_name("content.json")
data = json.loads(p.read_text(encoding="utf-8"))
root = data["sheets"][0]["root"]
print("root keys", list(root.keys()))


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def node_title(node: dict) -> str:
    d = node.get("data") if isinstance(node.get("data"), dict) else node
    for key in ("text", "title", "topic", "name", "html", "content"):
        if key in d and isinstance(d[key], str) and d[key].strip():
            return strip_html(d[key])
    # nested common patterns
    if isinstance(d.get("richText"), dict):
        return strip_html(json.dumps(d["richText"], ensure_ascii=False)[:80])
    return ""


def children_of(node: dict) -> list:
    for key in ("children", "leftChildren", "rightChildren"):
        if isinstance(node.get(key), list):
            return node[key]
    d = node.get("data")
    if isinstance(d, dict):
        for key in ("children", "leftChildren", "rightChildren"):
            if isinstance(d.get(key), list):
                return d[key]
    # some formats keep children at top and data separate
    kids = []
    if isinstance(node.get("children"), list):
        kids.extend(node["children"])
    return kids


def inspect(node, depth=0, maxd=3):
    if depth > maxd:
        return
    title = node_title(node)
    print("  " * depth + f"- {title!r} keys={list(node.keys())[:12]}")
    kids = children_of(node)
    # also check sibling containers
    for k in ("children", "leftChildren", "rightChildren"):
        if k in node and isinstance(node[k], list) and node[k]:
            print("  " * depth + f"  [{k}]={len(node[k])}")
    for child in kids[:5]:
        inspect(child, depth + 1, maxd)
    if len(kids) > 5:
        print("  " * (depth + 1) + f"... +{len(kids) - 5} more")


inspect(root, 0, 2)

# dump structure of first child's data keys more deeply
print("\n--- first-level children titles ---")
kids = children_of(root)
print("children count", len(kids))
for i, c in enumerate(kids):
    print(i, node_title(c), "child_keys", list(c.keys()))
    ck = children_of(c)
    print("   grandchildren", len(ck))
    for j, g in enumerate(ck[:8]):
        print("   ", j, node_title(g))
    if len(ck) > 8:
        print("    ...", len(ck) - 8, "more")

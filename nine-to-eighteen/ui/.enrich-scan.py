import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("lam", ROOT / "nine-to-eighteen/api/services/learn_article_md.py")
lam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lam)

seed = {i["slug"]: i for i in json.loads((ROOT / "core/data/learn_seed.json").read_text(encoding="utf-8"))}
rows = []
for path in sorted((ROOT / "nine-to-eighteen/ui/src/data/learn").rglob("*.md")):
    text = path.read_text(encoding="utf-8")
    if path.stem == "article-template" or not re.search(r"^slug:", text, re.M):
        continue
    payload, warnings = lam.parse_learn_article_md(text)
    slug = payload["slug"]
    st = payload.get("structured") or {}
    seed_st = (seed.get(slug) or {}).get("structured") or {}
    same = json.dumps(st, sort_keys=True, ensure_ascii=False) == json.dumps(seed_st, sort_keys=True, ensure_ascii=False)
    body = " ".join(s.get("body", "") for s in st.get("sections") or [])
    code = len(re.findall(r"```", body)) // 2
    words = len(re.findall(r"\w+", body))
    rows.append(
        (
            slug,
            path.parent.name,
            len(st.get("diagrams") or []),
            len(st.get("quiz") or []),
            len(st.get("anki") or []),
            code,
            words,
            len(st.get("sections") or []),
            same,
            len(warnings),
        )
    )
print("slug|dir|diag|quiz|anki|code|words|sections|md==seed|warn")
for row in rows:
    print("|".join(str(x) for x in row))
print("payload keys", sorted(payload))
print("structured keys", sorted(st))

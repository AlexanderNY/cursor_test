import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("lam", ROOT / "nine-to-eighteen/api/services/learn_article_md.py")
lam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lam)
seed = {i["slug"]: i for i in json.loads((ROOT / "core/data/learn_seed.json").read_text(encoding="utf-8"))}

for rel in sys.argv[1:]:
    payload, _ = lam.parse_learn_article_md((ROOT / rel).read_text(encoding="utf-8"))
    slug = payload["slug"]
    md_st, sd_st = payload["structured"], seed[slug]["structured"]
    print("==", slug)
    for key in sorted(set(md_st) | set(sd_st)):
        a, b = md_st.get(key), sd_st.get(key)
        if a != b:
            if isinstance(a, list) and isinstance(b, list):
                print(f"  {key}: md {len(a)} vs seed {len(b)}")
                for idx, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        print("    first diff at", idx)
                        print("     md  ", json.dumps(x, ensure_ascii=False)[:300])
                        print("     seed", json.dumps(y, ensure_ascii=False)[:300])
                        break
            else:
                print(f"  {key}: md {json.dumps(a, ensure_ascii=False)[:200]}")
                print(f"  {key}: seed {json.dumps(b, ensure_ascii=False)[:200]}")
    for key in ("theory", "lab", "diagram", "cheatsheet", "profiles", "publishedAt"):
        if payload.get(key) != seed[slug].get(key):
            print("  top", key, "differs")

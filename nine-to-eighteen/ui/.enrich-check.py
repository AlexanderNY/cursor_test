"""Usage: python .enrich-check.py <article.md> [...]"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "lam", ROOT / "nine-to-eighteen/api/services/learn_article_md.py"
)
lam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lam)

failed = False
for arg in sys.argv[1:]:
    path = pathlib.Path(arg)
    payload, warnings = lam.parse_learn_article_md(path.read_text(encoding="utf-8"))
    st = payload.get("structured") or {}
    body = "\n".join(s.get("body", "") for s in st.get("sections") or [])
    problems = list(warnings)
    for quiz in st.get("quiz") or []:
        words = len(quiz["answer"].split())
        if not quiz["answer"] or words > 5:
            problems.append(
                f"quiz answer must be 1-5 words: {quiz['question']!r} -> {quiz['answer']!r}"
            )
        if not quiz["explain"]:
            problems.append(f"quiz without explain: {quiz['question']!r}")
    if body.count("```") % 2:
        problems.append("unbalanced ``` in sections")
    print(
        f"{payload['slug']}: sections={len(st.get('sections') or [])} "
        f"diagrams={len(st.get('diagrams') or [])} quiz={len(st.get('quiz') or [])} "
        f"anki={len(st.get('anki') or [])} code={body.count('```') // 2} "
        f"lab={'yes' if st.get('lab') else 'NO'}"
    )
    for problem in problems:
        failed = True
        print("  PROBLEM:", problem)
sys.exit(1 if failed else 0)

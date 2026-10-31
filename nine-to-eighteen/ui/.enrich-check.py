"""Usage: python .enrich-check.py <article.md> [...]  — parse with site-api parser and report counts."""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("lam", ROOT / "nine-to-eighteen/api/services/learn_article_md.py")
lam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lam)

MERMAID_START = ("flowchart", "graph", "sequenceDiagram", "stateDiagram-v2", "erDiagram", "classDiagram", "journey", "quadrantChart")
failed = False
for arg in sys.argv[1:]:
    path = pathlib.Path(arg)
    payload, warnings = lam.parse_learn_article_md(path.read_text(encoding="utf-8"))
    st = payload.get("structured") or {}
    body = "\n".join(s.get("body", "") for s in st.get("sections") or [])
    problems = list(warnings)
    for quiz in st.get("quiz") or []:
        words = len(quiz["answer"].split())
        if not quiz["answer"] or words > 8:
            problems.append(f"quiz answer must be 1-8 words: {quiz['question']!r} -> {quiz['answer']!r}")
        if not quiz["explain"]:
            problems.append(f"quiz without explain: {quiz['question']!r}")
    for diagram in st.get("diagrams") or []:
        chart = diagram.get("mermaid", "").strip()
        if not chart.startswith(MERMAID_START):
            problems.append(f"diagram {diagram.get('caption')!r} starts with {chart[:20]!r}")
        if re.search(r"\[[^\]\"]*[()<>{}][^\]\"]*\]", chart):
            problems.append(f"diagram {diagram.get('caption')!r}: quote labels that contain ()<>{{}}")
    if body.count("```") % 2:
        problems.append("unbalanced ``` in sections")
    print(
        f"{payload['slug']}: sections={len(st.get('sections') or [])} diagrams={len(st.get('diagrams') or [])} "
        f"quiz={len(st.get('quiz') or [])} anki={len(st.get('anki') or [])} code={body.count('```') // 2} "
        f"lab={'yes' if st.get('lab') else 'NO'}"
    )
    for problem in problems:
        failed = True
        print("  PROBLEM:", problem)
sys.exit(1 if failed else 0)

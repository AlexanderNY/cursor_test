from __future__ import annotations

import html
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.db import fetch_all, fetch_one
from app.schemas.models import RunSummary


def _parse_summary(raw: str | None) -> dict[str, Any]:
    if not raw:
        return RunSummary().model_dump()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else RunSummary().model_dump()
    except json.JSONDecodeError:
        return RunSummary().model_dump()


def build_results_tree(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[int, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for row in rows:
        node = {
            "id": row["id"],
            "parent_id": row["parent_id"],
            "node_type": row["node_type"],
            "key": row.get("key"),
            "title": row.get("title"),
            "status": row["status"],
            "error": row.get("error"),
            "started_at": row.get("started_at").isoformat() if row.get("started_at") else None,
            "finished_at": row.get("finished_at").isoformat() if row.get("finished_at") else None,
            "duration_ms": row.get("duration_ms"),
            "sort_order": row.get("sort_order") or 0,
            "children": [],
        }
        by_id[node["id"]] = node
    for node in by_id.values():
        parent_id = node["parent_id"]
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    def sort_rec(items: list[dict[str, Any]]) -> None:
        items.sort(key=lambda n: n["sort_order"])
        for child in items:
            sort_rec(child["children"])

    sort_rec(roots)
    return roots


async def load_report_payload(run_id: int) -> dict[str, Any] | None:
    run = await fetch_one("SELECT * FROM runs WHERE id = %s", (run_id,))
    if run is None:
        return None
    scenario = await fetch_one(
        "SELECT id, name, format FROM scenarios WHERE id = %s",
        (run["scenario_id"],),
    )
    site = None
    if run.get("site_id"):
        site = await fetch_one(
            "SELECT id, name, base_url FROM sites WHERE id = %s",
            (run["site_id"],),
        )
    events = await fetch_all(
        "SELECT id, ts, level, message FROM run_events WHERE run_id = %s ORDER BY id ASC",
        (run_id,),
    )
    results = await fetch_all(
        """
        SELECT id, parent_id, node_type, key, title, status, error,
               started_at, finished_at, duration_ms, sort_order
        FROM run_results WHERE run_id = %s ORDER BY id ASC
        """,
        (run_id,),
    )
    artifacts = await fetch_all(
        """
        SELECT id, kind, path, step_name, result_id, created_at
        FROM artifacts WHERE run_id = %s ORDER BY id ASC
        """,
        (run_id,),
    )
    tree = build_results_tree(results)
    summary = _parse_summary(run.get("summary_json"))
    return {
        "run": {
            "id": run["id"],
            "status": run["status"],
            "scenario_id": run["scenario_id"],
            "scenario_name": scenario["name"] if scenario else None,
            "site_id": run.get("site_id"),
            "site_name": site["name"] if site else None,
            "base_url": run.get("base_url_snapshot"),
            "error_summary": run.get("error_summary"),
            "started_at": run.get("started_at").isoformat() if run.get("started_at") else None,
            "finished_at": run.get("finished_at").isoformat() if run.get("finished_at") else None,
            "created_at": run["created_at"].isoformat() if run.get("created_at") else None,
        },
        "summary": summary,
        "results": tree,
        "events": [
            {
                "id": e["id"],
                "ts": e["ts"].isoformat() if e.get("ts") else None,
                "level": e["level"],
                "message": e["message"],
            }
            for e in events
        ],
        "artifacts": [
            {
                "id": a["id"],
                "kind": a["kind"],
                "path": a["path"],
                "step_name": a.get("step_name"),
                "result_id": a.get("result_id"),
                "filename": Path(a["path"]).name,
            }
            for a in artifacts
        ],
    }


def _status_color(status: str) -> str:
    if status == "passed":
        return "#1a7f37"
    if status == "failed":
        return "#cf222e"
    return "#9a6700"


def _render_tree_html(nodes: list[dict[str, Any]], depth: int = 0) -> str:
    parts: list[str] = []
    for node in nodes:
        color = _status_color(str(node.get("status") or ""))
        indent = depth * 16
        title = html.escape(str(node.get("title") or node.get("key") or node["node_type"]))
        status = html.escape(str(node.get("status") or ""))
        err = html.escape(str(node.get("error") or ""))
        dur = node.get("duration_ms")
        dur_s = f"{dur} ms" if dur is not None else ""
        parts.append(
            f'<div style="margin-left:{indent}px;padding:4px 0;border-left:2px solid #ddd;'
            f'padding-left:8px;margin-bottom:2px">'
            f'<strong>{html.escape(node["node_type"])}</strong> {title} '
            f'<span style="color:{color};font-weight:600">{status}</span> '
            f'<span style="color:#666;font-size:12px">{dur_s}</span>'
        )
        if err:
            parts.append(f'<div style="color:#cf222e;font-size:13px">{err}</div>')
        parts.append("</div>")
        children = node.get("children") or []
        if children:
            parts.append(_render_tree_html(children, depth + 1))
    return "".join(parts)


def render_report_html(
    payload: dict[str, Any],
    *,
    artifact_src_prefix: str = "screenshots/",
    artifact_url_map: dict[str, str] | None = None,
) -> str:
    run = payload["run"]
    summary = payload.get("summary") or {}
    status = run.get("status") or ""
    status_color = _status_color(status)
    tree_html = _render_tree_html(payload.get("results") or [])
    arts = payload.get("artifacts") or []
    gallery = []
    for art in arts:
        if art.get("kind") != "screenshot":
            continue
        filename = str(art.get("filename") or "")
        name = html.escape(str(art.get("step_name") or filename))
        if artifact_url_map and filename in artifact_url_map:
            src = html.escape(artifact_url_map[filename])
        else:
            src = html.escape(artifact_src_prefix + filename)
        gallery.append(
            f'<figure style="margin:0">'
            f'<img src="{src}" alt="{name}" style="max-width:100%;border:1px solid #ddd" />'
            f"<figcaption>{name}</figcaption></figure>"
        )
    events = payload.get("events") or []
    event_lines = "\n".join(
        html.escape(f"[{e.get('ts')}] {e.get('level')} {e.get('message')}") for e in events
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>E2E Report #{run.get("id")}</title>
  <style>
    body {{ font-family: Segoe UI, system-ui, sans-serif; margin: 24px; color: #1f2328; }}
    h1 {{ margin: 0 0 8px; }}
    .meta {{ color: #656d76; margin-bottom: 16px; }}
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
              background: {status_color}; color: #fff; font-weight: 600; }}
    .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
    .card {{ border: 1px solid #d0d7de; border-radius: 8px; padding: 12px 16px; min-width: 120px; }}
    .card strong {{ display: block; font-size: 1.4rem; }}
    pre {{ background: #f6f8fa; padding: 12px; overflow: auto; border-radius: 8px; font-size: 12px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }}
  </style>
</head>
<body>
  <h1>E2E Report #{html.escape(str(run.get("id")))}</h1>
  <div class="meta">
    Status: <span class="badge">{html.escape(status)}</span><br/>
    Scenario: {html.escape(str(run.get("scenario_name") or run.get("scenario_id")))}<br/>
    Site: {html.escape(str(run.get("site_name") or "—"))}<br/>
    Base URL: {html.escape(str(run.get("base_url") or "—"))}<br/>
    Started: {html.escape(str(run.get("started_at") or "—"))}<br/>
    Finished: {html.escape(str(run.get("finished_at") or "—"))}<br/>
    Error: {html.escape(str(run.get("error_summary") or "—"))}
  </div>
  <div class="cards">
    <div class="card"><strong>{summary.get("sections_passed", 0)}</strong>sections passed</div>
    <div class="card"><strong>{summary.get("sections_failed", 0)}</strong>sections failed</div>
    <div class="card"><strong>{summary.get("actions_passed", 0)}</strong>actions passed</div>
    <div class="card"><strong>{summary.get("actions_failed", 0)}</strong>actions failed</div>
    <div class="card"><strong>{summary.get("actions_skipped", 0)}</strong>actions skipped</div>
  </div>
  <h2>Results tree</h2>
  {tree_html or "<p>No structured results.</p>"}
  <h2>Screenshots</h2>
  <div class="gallery">{"".join(gallery) or "<p>No screenshots.</p>"}</div>
  <h2>Event log</h2>
  <pre>{event_lines or "—"}</pre>
</body>
</html>
"""


async def build_report_zip_bytes(run_id: int) -> bytes | None:
    payload = await load_report_payload(run_id)
    if payload is None:
        return None
    settings = get_settings()
    html_doc = render_report_html(payload, artifact_src_prefix="screenshots/")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.html", html_doc)
        zf.writestr("report.json", json.dumps(payload, ensure_ascii=False, indent=2))
        for art in payload.get("artifacts") or []:
            if art.get("kind") != "screenshot":
                continue
            disk = settings.artifacts_path / art["path"]
            if disk.is_file():
                zf.write(disk, arcname=f"screenshots/{art['filename']}")
    return buf.getvalue()

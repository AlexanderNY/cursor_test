"""Build PDF (Playwright) and DOCX (python-docx) from resume preview data."""
from __future__ import annotations

import html
from io import BytesIO
from pathlib import Path
from typing import Any

from services.text_sanitize import sanitize_plain_text

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def _selected_projects(projects: Any, *, max_count: int = 6) -> list[dict[str, Any]]:
    if not isinstance(projects, list):
        return []
    out: list[dict[str, Any]] = []
    for raw in projects:
        if not isinstance(raw, dict) or not raw.get("selected"):
            continue
        name = str(raw.get("name") or "").strip()
        url = str(raw.get("url") or "").strip()
        if not name or not url:
            continue
        out.append(
            {
                "name": name,
                "url": url,
                "description": str(raw.get("description") or "").strip(),
                "language": str(raw.get("language") or "").strip(),
                "stars": int(raw.get("stars") or 0),
            }
        )
        if len(out) >= max_count:
            break
    return out


def _full_name(profile: dict[str, Any], username: str) -> str:
    parts = [
        str(profile.get("lastName") or ""),
        str(profile.get("firstName") or ""),
        str(profile.get("patronymic") or ""),
    ]
    joined = " ".join(p for p in parts if p).strip()
    return joined or username or "Кандидат"


def render_resume_html(
    *,
    profile: dict[str, Any],
    resume: dict[str, Any],
    skills: list[dict[str, Any]],
    username: str,
) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    name = _full_name(profile, username)
    salary = resume.get("salaryAmount")
    salary_text = (
        f"{salary} {resume.get('salaryCurrency') or 'RUB'}"
        if salary is not None
        else "не указан"
    )
    about_raw = sanitize_plain_text(str(resume.get("about") or ""))
    about_html = html.escape(about_raw).replace("\n", "<br/>") if about_raw else "—"
    skill_labels = [
        str(s.get("display") or s.get("name") or "").strip()
        for s in skills
        if str(s.get("display") or s.get("name") or "").strip()
    ]

    badge_labels: list[str] = []
    for raw in resume.get("selectedBadgeIds") or []:
        label = str(raw or "").strip()
        if label:
            badge_labels.append(label)
    # Prefer human titles if caller passed badgeTitles
    titles = resume.get("badgeTitles")
    if isinstance(titles, list) and titles:
        badge_labels = [str(t).strip() for t in titles if str(t).strip()]

    projects = _selected_projects(resume.get("githubProjects") or [])

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("resume_hh.html")
    return template.render(
        name=name,
        city=str(profile.get("city") or "—"),
        birth=str(profile.get("birthDate") or ""),
        phone=str(profile.get("phone") or "—"),
        email=str(profile.get("email") or "—"),
        citizenship=str(profile.get("citizenship") or "—"),
        trips="готов" if profile.get("readyForTrips") else "не готов",
        specialization=str(resume.get("specialization") or resume.get("title") or "—"),
        version=str(resume.get("versionName") or ""),
        salary=salary_text,
        about=about_html,
        skills=skill_labels,
        badges=badge_labels,
        projects=projects,
    )


async def build_pdf_bytes(html_doc: str) -> bytes:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            page = await browser.new_page()
            await page.set_content(html_doc, wait_until="networkidle")
            pdf = await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
            )
            return bytes(pdf)
        finally:
            await browser.close()


def build_docx_bytes(
    *,
    profile: dict[str, Any],
    resume: dict[str, Any],
    skills: list[dict[str, Any]],
    username: str,
) -> bytes:
    from docx import Document
    from docx.shared import Pt, RGBColor

    doc = Document()
    name = _full_name(profile, username)
    title = doc.add_heading(name, level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0xD6, 0x00, 0x1C)

    meta = doc.add_paragraph()
    meta_bits = [
        str(profile.get("city") or ""),
        str(profile.get("birthDate") or ""),
        str(profile.get("phone") or ""),
        str(profile.get("email") or ""),
    ]
    meta.add_run(" · ".join(b for b in meta_bits if b))

    version = str(resume.get("versionName") or "").strip()
    if version:
        doc.add_paragraph(f"Версия: {version}")

    doc.add_heading("Желаемая должность", level=2)
    doc.add_paragraph(str(resume.get("specialization") or resume.get("title") or "—"))
    salary = resume.get("salaryAmount")
    salary_line = (
        f"{salary} {resume.get('salaryCurrency') or 'RUB'}"
        if salary is not None
        else "не указан"
    )
    doc.add_paragraph(f"Оклад: {salary_line}")

    employment = resume.get("employmentTypes") or []
    work_formats = resume.get("workFormats") or []
    if employment:
        doc.add_paragraph("Занятость: " + ", ".join(str(x) for x in employment))
    if work_formats:
        doc.add_paragraph("Формат: " + ", ".join(str(x) for x in work_formats))

    doc.add_heading("О себе", level=2)
    about = sanitize_plain_text(str(resume.get("about") or "")) or "—"
    paragraph = doc.add_paragraph(about)
    for run in paragraph.runs:
        run.font.size = Pt(11)

    doc.add_heading("Ключевые навыки", level=2)
    if skills:
        for skill in skills:
            doc.add_paragraph(
                str(skill.get("display") or skill.get("name") or ""),
                style="List Bullet",
            )
    else:
        doc.add_paragraph("—")

    badge_titles = resume.get("badgeTitles")
    if isinstance(badge_titles, list) and badge_titles:
        labels = [str(t).strip() for t in badge_titles if str(t).strip()]
    else:
        labels = [str(x).strip() for x in (resume.get("selectedBadgeIds") or []) if str(x).strip()]
    if labels:
        doc.add_heading("Достижения", level=2)
        for label in labels:
            doc.add_paragraph(label, style="List Bullet")

    projects = _selected_projects(resume.get("githubProjects") or [])
    if projects:
        doc.add_heading("Проекты", level=2)
        for project in projects:
            line = str(project.get("name") or "")
            lang = str(project.get("language") or "").strip()
            if lang:
                line += f" · {lang}"
            stars = int(project.get("stars") or 0)
            if stars:
                line += f" · ★{stars}"
            doc.add_paragraph(line, style="List Bullet")
            desc = str(project.get("description") or "").strip()
            if desc:
                doc.add_paragraph(desc)
            url = str(project.get("url") or "").strip()
            if url:
                doc.add_paragraph(url)

    footer = doc.add_paragraph("Собрано на 9to18.ru")
    for run in footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

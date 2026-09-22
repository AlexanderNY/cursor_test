"""Минимальная схема resume-api (таблицы уже есть в site-api; IF NOT EXISTS)."""

SITE_RESUMES_TABLE = """
CREATE TABLE IF NOT EXISTS site_resumes (
    user_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL DEFAULT '',
    specialization VARCHAR(255) NOT NULL DEFAULT '',
    salary_amount INT,
    salary_currency VARCHAR(8) NOT NULL DEFAULT 'RUB',
    employment_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    work_formats JSONB NOT NULL DEFAULT '[]'::jsonb,
    about TEXT NOT NULL DEFAULT '',
    selected_skill_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    questionnaire_answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

RESUME_SCHEMA_PATCHES: list[str] = [
    """
    ALTER TABLE site_resumes
    ADD COLUMN IF NOT EXISTS questionnaire_answers JSONB NOT NULL DEFAULT '{}'::jsonb
    """,
]

RESUME_TABLES: list[str] = [SITE_RESUMES_TABLE] + RESUME_SCHEMA_PATCHES

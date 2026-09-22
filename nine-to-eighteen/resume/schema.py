"""Схема resume-api: несколько резюме на пользователя + файлы экспорта."""

# Fresh installs
SITE_RESUMES_TABLE = """
CREATE TABLE IF NOT EXISTS site_resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    version_name VARCHAR(120) NOT NULL DEFAULT 'Основное',
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SITE_RESUME_EXPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS site_resume_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    resume_id UUID NOT NULL,
    format VARCHAR(8) NOT NULL,
    file_name VARCHAR(255) NOT NULL DEFAULT '',
    storage_key VARCHAR(512) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);
"""

# Idempotent migration from legacy PK(user_id) → UUID id
MIGRATE_SITE_RESUMES_TO_MULTI = """
DO $migrate$
BEGIN
  CREATE EXTENSION IF NOT EXISTS pgcrypto;

  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'site_resumes'
  ) AND EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'site_resumes' AND column_name = 'user_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'site_resumes' AND column_name = 'id'
  ) THEN
    ALTER TABLE site_resumes RENAME TO site_resumes_legacy_v1;

    CREATE TABLE site_resumes (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id INT NOT NULL,
      version_name VARCHAR(120) NOT NULL DEFAULT 'Основное',
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
      created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO site_resumes (
      id, user_id, version_name, title, specialization, salary_amount, salary_currency,
      employment_types, work_formats, about, selected_skill_keys, generated_skills,
      questionnaire_answers, created_at, updated_at
    )
    SELECT
      gen_random_uuid(),
      user_id,
      'Основное',
      COALESCE(title, ''),
      COALESCE(specialization, ''),
      salary_amount,
      COALESCE(salary_currency, 'RUB'),
      COALESCE(employment_types, '[]'::jsonb),
      COALESCE(work_formats, '[]'::jsonb),
      COALESCE(about, ''),
      COALESCE(selected_skill_keys, '[]'::jsonb),
      COALESCE(generated_skills, '[]'::jsonb),
      COALESCE(questionnaire_answers, '{}'::jsonb),
      COALESCE(updated_at, CURRENT_TIMESTAMP),
      COALESCE(updated_at, CURRENT_TIMESTAMP)
    FROM site_resumes_legacy_v1;

    DROP TABLE site_resumes_legacy_v1;
  END IF;
END
$migrate$;
"""

RESUME_SCHEMA_PATCHES: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    MIGRATE_SITE_RESUMES_TO_MULTI,
    """
    ALTER TABLE site_resumes
    ADD COLUMN IF NOT EXISTS version_name VARCHAR(120) NOT NULL DEFAULT 'Основное'
    """,
    """
    ALTER TABLE site_resumes
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    """,
    """
    ALTER TABLE site_resumes
    ADD COLUMN IF NOT EXISTS questionnaire_answers JSONB NOT NULL DEFAULT '{}'::jsonb
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_site_resumes_user_updated
    ON site_resumes (user_id, updated_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_site_resume_exports_user
    ON site_resume_exports (user_id, created_at DESC)
    """,
]

RESUME_TABLES: list[str] = [
    SITE_RESUMES_TABLE,
    SITE_RESUME_EXPORTS_TABLE,
] + RESUME_SCHEMA_PATCHES

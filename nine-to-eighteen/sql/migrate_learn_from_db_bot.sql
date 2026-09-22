-- One-shot: copy learn_posts from db_bot into db_9to18 (same Postgres cluster).
-- Run as superuser connected to db_9to18:
--   psql -U postgres -d db_9to18 -f migrate_learn_from_db_bot.sql
--
-- Requires dblink extension OR run the INSERT…SELECT via postgres_fdw.
-- Simpler alternative if dblink unavailable: export/import JSON via site-api reset-to-seed
-- and/or pg_dump -t learn_posts db_bot | sed … | psql db_9to18

CREATE EXTENSION IF NOT EXISTS dblink;

-- Ensure target table exists (also created by site-api schema init)
-- Then copy rows (skip conflicts on slug)

INSERT INTO learn_posts (
    slug, episode, title, short_title, rubric_id, sort_order,
    theory, lab, cheatsheet, diagram, links, structured,
    theory_format, lab_format, cheatsheet_format,
    profiles, level, tags, excerpt, duration_min, prerequisites,
    author, author_url, cover_url, seo_title, seo_description,
    seo_keywords, canonical_url, published_at, updated_at, created_at
)
SELECT
    slug, episode, title, short_title, rubric_id, sort_order,
    theory, lab, cheatsheet, diagram, links, structured,
    theory_format, lab_format, cheatsheet_format,
    profiles, level, tags, excerpt, duration_min, prerequisites,
    author, author_url, cover_url, seo_title, seo_description,
    seo_keywords, canonical_url, published_at, updated_at, created_at
FROM dblink(
    'dbname=db_bot',
    $q$
    SELECT
        slug, episode, title, short_title, rubric_id, sort_order,
        theory, lab, cheatsheet, diagram, links, structured,
        theory_format, lab_format, cheatsheet_format,
        profiles, level, tags, excerpt, duration_min, prerequisites,
        author, author_url, cover_url, seo_title, seo_description,
        seo_keywords, canonical_url, published_at, updated_at, created_at
    FROM learn_posts
    $q$
) AS remote (
    slug VARCHAR(128),
    episode VARCHAR(32),
    title VARCHAR(512),
    short_title VARCHAR(128),
    rubric_id VARCHAR(64),
    sort_order INTEGER,
    theory TEXT,
    lab TEXT,
    cheatsheet TEXT,
    diagram TEXT,
    links JSONB,
    structured JSONB,
    theory_format VARCHAR(16),
    lab_format VARCHAR(16),
    cheatsheet_format VARCHAR(16),
    profiles JSONB,
    level VARCHAR(16),
    tags JSONB,
    excerpt TEXT,
    duration_min INTEGER,
    prerequisites JSONB,
    author VARCHAR(128),
    author_url VARCHAR(512),
    cover_url VARCHAR(1024),
    seo_title VARCHAR(200),
    seo_description VARCHAR(400),
    seo_keywords JSONB,
    canonical_url VARCHAR(512),
    published_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ
)
ON CONFLICT (slug) DO NOTHING;

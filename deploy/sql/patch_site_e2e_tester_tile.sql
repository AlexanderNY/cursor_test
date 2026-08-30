-- Replace Quiz tile with E2E Tester on already-seeded db_9to18.
-- Optional if core upsert (_upsert_featured_apps) already ran.

INSERT INTO site_apps (
    slug, title, subtitle, description, accent, emoji,
    external_href, app_path, is_visible, sort_order
) VALUES (
    'e2e-tester',
    'E2E Tester',
    'Playwright · сценарии',
    'On-demand браузерные E2E против живого стека: YAML/JSON шаги, Playwright-скрипты, креды и артефакты прогонов.',
    '#f43f5e',
    '🧪',
    'http://127.0.0.1:8300',
    '',
    TRUE,
    3
)
ON CONFLICT (slug) DO UPDATE SET
    title = EXCLUDED.title,
    subtitle = EXCLUDED.subtitle,
    description = EXCLUDED.description,
    accent = EXCLUDED.accent,
    emoji = EXCLUDED.emoji,
    external_href = EXCLUDED.external_href,
    is_visible = TRUE,
    sort_order = EXCLUDED.sort_order,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO site_posts (app_slug, slug, title, body, is_published)
VALUES (
    'e2e-tester',
    'about',
    'О приложении E2E Tester',
    E'## E2E Tester\n\nOn-demand сервис браузерных E2E (Playwright).\n\nПанель: http://127.0.0.1:8300',
    TRUE
)
ON CONFLICT (app_slug, slug) DO UPDATE SET
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    updated_at = CURRENT_TIMESTAMP;

UPDATE site_apps
SET is_visible = FALSE, updated_at = CURRENT_TIMESTAMP
WHERE slug = 'quiz' AND is_visible = TRUE;

-- Add / refresh «Карта обучения» tile on db_9to18.
INSERT INTO site_apps (
    slug, title, subtitle, description, accent, emoji,
    external_href, app_path, is_visible, sort_order
) VALUES (
    'learning-map',
    'Карта обучения',
    'Mind map · собеседование',
    'Интерактивная карта подготовки к собеседованию: ветки тем и конспект из Markdown.',
    '#2dd4bf',
    '🗺️',
    '',
    '/game/learning-map',
    TRUE,
    3
)
ON CONFLICT (slug) DO UPDATE SET
    title = EXCLUDED.title,
    subtitle = EXCLUDED.subtitle,
    description = EXCLUDED.description,
    accent = EXCLUDED.accent,
    emoji = EXCLUDED.emoji,
    app_path = EXCLUDED.app_path,
    is_visible = TRUE,
    sort_order = EXCLUDED.sort_order,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO site_posts (app_slug, slug, title, body, is_published)
VALUES (
    'learning-map',
    'about',
    'О приложении Карта обучения',
    E'## Карта обучения\n\nИнтерактивная mind map подготовки к собеседованию на основе Markdown-конспекта.\n\nОткрыть: [/game/learning-map](/game/learning-map)',
    TRUE
)
ON CONFLICT (app_slug, slug) DO UPDATE SET
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    updated_at = CURRENT_TIMESTAMP;

-- Hide legacy stub tiles; ensure live Code tile is visible.
-- Safe to re-run.

UPDATE site_apps
SET is_visible = FALSE, updated_at = CURRENT_TIMESTAMP
WHERE slug IN (
  'e2e-tester', 'menu', 'rating', 'events', 'help', 'chat',
  'stream', 'news', 'forum', 'map', 'team'
)
AND is_visible = TRUE;

INSERT INTO site_apps (
  slug, title, subtitle, description, accent, emoji,
  external_href, app_path, is_visible, sort_order
) VALUES (
  'code',
  'Code',
  'Python в браузере',
  'Песочница Pyodide: короткие упражнения без IDE. Лабы Learn можно запускать отсюда.',
  '#2dd4bf',
  '⌨️',
  '',
  '/game/code',
  TRUE,
  4
)
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  subtitle = EXCLUDED.subtitle,
  description = EXCLUDED.description,
  accent = EXCLUDED.accent,
  emoji = EXCLUDED.emoji,
  app_path = EXCLUDED.app_path,
  is_visible = TRUE,
  updated_at = CURRENT_TIMESTAMP;

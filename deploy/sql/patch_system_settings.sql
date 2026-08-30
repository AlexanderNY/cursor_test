-- Runtime settings (AI toggle, onboarding prefs, etc.)
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO system_settings (key, value)
VALUES ('ai_enabled', 'true'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_settings (key, value)
VALUES (
    'site_9to18_promo',
    '{
      "enabled": true,
      "serviceSlug": "copyparse",
      "eyebrow": "Спотлайт · взаимное продвижение",
      "title": "CopyParse: SaaS кросспостинга как живой стенд",
      "body": "9to18 — площадка взаимного продвижения проектов. Сейчас в фокусе CopyParse: бренды, каналы, календарь и inbox — тот же стек, который разбираем в Learn. Поддержите развитие сервиса и загляните на стенд.",
      "ctaLabel": "Открыть copyparse.ru",
      "ctaHref": "https://www.copyparse.ru"
    }'::jsonb
)
ON CONFLICT (key) DO NOTHING;

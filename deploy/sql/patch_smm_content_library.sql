-- Content library: brand templates + media packs (plan 2.3)
CREATE TABLE IF NOT EXISTS smm_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('prompt', 'cta', 'utm', 'post_body')),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_templates_brand
    ON smm_templates(brand_id, kind);
CREATE INDEX IF NOT EXISTS idx_smm_templates_user
    ON smm_templates(user_id);

CREATE TABLE IF NOT EXISTS smm_media_packs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    object_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_media_packs_brand
    ON smm_media_packs(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_media_packs_user
    ON smm_media_packs(user_id);

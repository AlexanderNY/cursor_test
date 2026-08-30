-- Season funnel attribution + demo brands (idempotent).
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_source VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_medium VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_campaign VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS growth_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    utm_source VARCHAR(64),
    utm_medium VARCHAR(64),
    utm_campaign VARCHAR(128),
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_growth_events_campaign
    ON growth_events (utm_campaign, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_growth_events_type_created
    ON growth_events (event_type, created_at DESC);

DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

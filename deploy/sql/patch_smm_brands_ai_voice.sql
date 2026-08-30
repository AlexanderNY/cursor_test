-- Brand tone-of-voice + prompt snippets (plan 1.3 AI product layer)
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN tone_of_voice TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN style_notes TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN prompt_snippets JSONB NOT NULL DEFAULT '[]'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- Competitors monitoring: snapshot normalization, inbox type, unique dedup.
-- Safe to re-run.

DO $$
BEGIN
    ALTER TABLE smm_competitor_snapshots ADD COLUMN IF NOT EXISTS post_url TEXT;
    ALTER TABLE smm_competitor_snapshots ADD COLUMN IF NOT EXISTS text_hash VARCHAR(64);
EXCEPTION WHEN others THEN NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_smm_competitor_external_post
    ON smm_competitor_snapshots (channel_id, external_post_id)
    WHERE external_post_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_smm_competitor_text_hash
    ON smm_competitor_snapshots (channel_id, text_hash)
    WHERE text_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_smm_competitor_posted_at
    ON smm_competitor_snapshots (channel_id, posted_at DESC NULLS LAST);

-- Inbox: competitor_post type + url network
DO $$
DECLARE
    con_name text;
BEGIN
    SELECT c.conname INTO con_name
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'smm_inbox_items'
      AND c.contype = 'c'
      AND pg_get_constraintdef(c.oid) ILIKE '%type%';

    IF con_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE smm_inbox_items DROP CONSTRAINT %I', con_name);
    END IF;

    ALTER TABLE smm_inbox_items
        ADD CONSTRAINT smm_inbox_items_type_check
        CHECK (type IN ('dm', 'comment', 'reaction', 'competitor_post'));

    con_name := NULL;
    SELECT c.conname INTO con_name
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'smm_inbox_items'
      AND c.contype = 'c'
      AND pg_get_constraintdef(c.oid) ILIKE '%network%';

    IF con_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE smm_inbox_items DROP CONSTRAINT %I', con_name);
    END IF;

    ALTER TABLE smm_inbox_items
        ADD CONSTRAINT smm_inbox_items_network_check
        CHECK (network IN (
            'tg', 'vk', 'url',
            'instagram', 'threads', 'tw', 'dzen', 'wp'
        ));
END $$;

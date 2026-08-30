-- Expand smm_brand_channels / smm_inbox_items networks beyond tg|vk|url.
-- Safe to re-run: drops matching check constraints, then recreates.

DO $$
DECLARE
    con_name text;
BEGIN
    -- smm_brand_channels.network
    SELECT c.conname INTO con_name
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'smm_brand_channels'
      AND c.contype = 'c'
      AND pg_get_constraintdef(c.oid) ILIKE '%network%';

    IF con_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE smm_brand_channels DROP CONSTRAINT %I', con_name);
    END IF;

    ALTER TABLE smm_brand_channels
        ALTER COLUMN network TYPE VARCHAR(20);

    ALTER TABLE smm_brand_channels
        ADD CONSTRAINT smm_brand_channels_network_check
        CHECK (network IN (
            'tg', 'vk', 'url',
            'instagram', 'threads', 'tw', 'dzen', 'wp'
        ));

    -- smm_inbox_items.network
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
        ALTER COLUMN network TYPE VARCHAR(20);

    ALTER TABLE smm_inbox_items
        ADD CONSTRAINT smm_inbox_items_network_check
        CHECK (network IN (
            'tg', 'vk', 'url',
            'instagram', 'threads', 'tw', 'dzen', 'wp'
        ));
END $$;

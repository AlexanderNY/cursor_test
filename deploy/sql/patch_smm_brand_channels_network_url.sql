-- Allow URL sources as brand channels (network = 'url', typically role = 'source').
-- Safe to re-run: drops old check if present, then recreates.

DO $$
DECLARE
    con_name text;
BEGIN
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
        ADD CONSTRAINT smm_brand_channels_network_check
        CHECK (network IN ('tg', 'vk', 'url'));
END $$;

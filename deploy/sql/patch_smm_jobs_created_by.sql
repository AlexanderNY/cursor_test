-- Attribution: who created the publish job (may differ from credential owner user_id)
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN created_by_user_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
UPDATE smm_publish_jobs
SET created_by_user_id = COALESCE(assigned_to, user_id)
WHERE created_by_user_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_created_by
    ON smm_publish_jobs(created_by_user_id)
    WHERE created_by_user_id IS NOT NULL;

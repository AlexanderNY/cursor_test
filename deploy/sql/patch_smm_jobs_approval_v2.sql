-- Content OS 2.1: approve workflow v2 (assigned_to, rejection_comment)
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN assigned_to INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN rejection_comment TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_assigned_to
    ON smm_publish_jobs(assigned_to)
    WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_status
    ON smm_publish_jobs(user_id, status);

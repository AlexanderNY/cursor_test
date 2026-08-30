-- VK auth: 4 блока (community / callback / app / oauth) — секреты в vk_profiles
DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_callback_confirmation VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_callback_secret VARCHAR(256);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_app_service_key VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE vk_profiles ALTER COLUMN access_token TYPE TEXT;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE vk_profiles ALTER COLUMN user_access_token TYPE TEXT;
EXCEPTION WHEN others THEN NULL; END $$;

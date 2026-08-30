-- VK app secrets: avoid truncation of protected / service keys
ALTER TABLE vk_profiles ALTER COLUMN vk_app_secret TYPE TEXT;
ALTER TABLE vk_profiles ALTER COLUMN vk_app_service_key TYPE TEXT;
ALTER TABLE vk_profiles ALTER COLUMN vk_callback_secret TYPE TEXT;

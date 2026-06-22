"""SQL схемы для создания таблиц базы данных."""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'guest' NOT NULL CHECK (role IN ('guest', 'user', 'admin', 'manager', 'author')),
    tariff VARCHAR(50) DEFAULT 'free' NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

ADD_TARIFF_TO_USERS = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS tariff VARCHAR(50) DEFAULT 'free' NOT NULL;
"""

ADD_IS_BLOCKED_TO_USERS = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE NOT NULL;
"""

CREATE_REFRESH_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_BLACKLISTED_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS blacklisted_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PASSWORD_RESET_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_EMAIL_VERIFICATION_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_ROLE_TARIFF_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS user_role_tariff_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    role_old VARCHAR(20) NULL,
    role_new VARCHAR(20) NULL,
    tariff_old VARCHAR(50) NULL,
    tariff_new VARCHAR(50) NULL
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_blacklisted_tokens_token ON blacklisted_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_user_role_tariff_history_user_id ON user_role_tariff_history(user_id);
"""

ALTER_USERS_ROLE_CHECK = """
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('guest', 'user', 'admin', 'manager', 'author'));
"""

CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
);
"""

CREATE_GROUP_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_in_group VARCHAR(20) NOT NULL CHECK (role_in_group IN ('manager', 'author')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
"""

CREATE_GROUP_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id);
"""

ADD_GROUPS_DESCRIPTION = """
ALTER TABLE groups ADD COLUMN IF NOT EXISTS description TEXT;
"""

# Один пользователь может быть в нескольких группах: уникальность (group_id, user_id)
GROUP_MEMBERS_DROP_USER_UNIQUE = """
ALTER TABLE group_members DROP CONSTRAINT IF EXISTS group_members_user_id_key;
"""

GROUP_MEMBERS_ADD_GROUP_USER_UNIQUE = """
ALTER TABLE group_members DROP CONSTRAINT IF EXISTS group_members_group_id_user_id_key;
ALTER TABLE group_members ADD CONSTRAINT group_members_group_id_user_id_key UNIQUE (group_id, user_id);
"""

# Биллинг: внешний провайдер, подписка, статус
BILLING_USERS_COLUMNS = """
DO $$
BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_provider VARCHAR(32);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_customer_id VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_subscription_id VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(40);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMP;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

CREATE_PLAN_DEFINITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS plan_definitions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    description TEXT,
    limits_json JSONB NOT NULL DEFAULT '{}',
    sort_order INTEGER DEFAULT 0
);
"""

CREATE_BILLING_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS billing_events (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    event_id VARCHAR(255),
    event_type VARCHAR(120) NOT NULL,
    payload_json JSONB,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_billing_events_user_id ON billing_events(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_created_at ON billing_events(created_at);
"""

CREATE_ADMIN_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(80),
    details_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created_at ON admin_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin_user_id ON admin_audit_log(admin_user_id);
"""

# Идемпотентность Stripe webhooks: один event_id на провайдера
BILLING_EVENTS_UNIQUE_PROVIDER_EVENT = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_events_provider_event_id
ON billing_events (provider, event_id);
"""

ALL_TABLES = [
    CREATE_USERS_TABLE,
    ADD_TARIFF_TO_USERS,
    ADD_IS_BLOCKED_TO_USERS,
    CREATE_USER_ROLE_TARIFF_HISTORY_TABLE,
    ALTER_USERS_ROLE_CHECK,
    CREATE_GROUPS_TABLE,
    CREATE_GROUP_MEMBERS_TABLE,
    CREATE_GROUP_INDEXES,
    ADD_GROUPS_DESCRIPTION,
    GROUP_MEMBERS_DROP_USER_UNIQUE,
    GROUP_MEMBERS_ADD_GROUP_USER_UNIQUE,
    BILLING_USERS_COLUMNS,
    CREATE_PLAN_DEFINITIONS_TABLE,
    CREATE_BILLING_EVENTS_TABLE,
    BILLING_EVENTS_UNIQUE_PROVIDER_EVENT,
    CREATE_ADMIN_AUDIT_LOG_TABLE,
    CREATE_REFRESH_TOKENS_TABLE,
    CREATE_BLACKLISTED_TOKENS_TABLE,
    CREATE_PASSWORD_RESET_TOKENS_TABLE,
    CREATE_EMAIL_VERIFICATION_TOKENS_TABLE,
    CREATE_INDEXES,
]


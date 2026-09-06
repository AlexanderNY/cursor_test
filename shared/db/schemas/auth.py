"""Auth service DDL."""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'guest' NOT NULL
        CHECK (role IN ('guest', 'user', 'admin', 'manager', 'author')),
    tariff VARCHAR(50) DEFAULT 'free' NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE NOT NULL,
    billing_provider VARCHAR(32),
    billing_customer_id VARCHAR(255),
    billing_subscription_id VARCHAR(255),
    subscription_status VARCHAR(40),
    subscription_current_period_end TIMESTAMPTZ,
    utm_source VARCHAR(64),
    utm_medium VARCHAR(64),
    utm_campaign VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USERS_UTM_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_source VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_medium VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_campaign VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

CREATE_GROWTH_EVENTS_TABLE = """
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
"""

CREATE_REFRESH_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_BLACKLISTED_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS blacklisted_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PASSWORD_RESET_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_EMAIL_VERIFICATION_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_ROLE_TARIFF_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS user_role_tariff_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    role_old VARCHAR(20) NULL,
    role_new VARCHAR(20) NULL,
    tariff_old VARCHAR(50) NULL,
    tariff_new VARCHAR(50) NULL
);
"""

CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
);
"""

CREATE_GROUP_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_in_group VARCHAR(20) NOT NULL
        CHECK (role_in_group IN ('admin', 'editor', 'analyst')),
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (group_id, user_id)
);
"""

CREATE_GROUP_INVITES_TABLE = """
CREATE TABLE IF NOT EXISTS group_invites (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    email VARCHAR(255),
    role_in_group VARCHAR(20) NOT NULL
        CHECK (role_in_group IN ('admin', 'editor', 'analyst')),
    token VARCHAR(64) UNIQUE NOT NULL,
    invited_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'revoked', 'expired')),
    accepted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_group_invites_token ON group_invites(token);
CREATE INDEX IF NOT EXISTS idx_group_invites_group_status ON group_invites(group_id, status);
CREATE INDEX IF NOT EXISTS idx_group_invites_email
    ON group_invites(email) WHERE email IS NOT NULL;
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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ADMIN_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(80),
    details_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PROMO_CODES_TABLE = """
CREATE TABLE IF NOT EXISTS promo_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(40) UNIQUE NOT NULL,
    description TEXT,
    discount_percent INTEGER NULL CHECK (discount_percent IS NULL OR (discount_percent >= 1 AND discount_percent <= 100)),
    discount_amount INTEGER NULL CHECK (discount_amount IS NULL OR discount_amount >= 0),
    applies_to_tariff VARCHAR(50) NULL,
    max_redemptions INTEGER NULL,
    redeemed_count INTEGER NOT NULL DEFAULT 0,
    valid_from TIMESTAMPTZ NULL,
    valid_until TIMESTAMPTZ NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes (code);
"""

CREATE_BILLING_PLAN_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS billing_plan_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_tariff VARCHAR(50) NOT NULL,
    requested_tariff VARCHAR(50) NOT NULL,
    promo_code VARCHAR(40) NULL,
    list_price INTEGER NOT NULL DEFAULT 0,
    discount_amount INTEGER NOT NULL DEFAULT 0,
    final_price INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(8) NOT NULL DEFAULT 'RUB',
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'invoiced', 'applied', 'rejected', 'cancelled')),
    invoice_sent_at TIMESTAMPTZ NULL,
    invoice_smtp_sent BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_body TEXT NULL,
    admin_comment TEXT NULL,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    processed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_billing_plan_requests_user_status
    ON billing_plan_requests (user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_plan_requests_status
    ON billing_plan_requests (status, created_at DESC);
"""

CREATE_PROMO_CODE_REDEMPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS promo_code_redemptions (
    id SERIAL PRIMARY KEY,
    promo_code_id INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id INTEGER NULL REFERENCES billing_plan_requests(id) ON DELETE SET NULL,
    used_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (promo_code_id, user_id)
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
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_events_user_id ON billing_events(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_created_at ON billing_events(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_events_provider_event_id
    ON billing_events (provider, event_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created_at ON admin_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin_user_id ON admin_audit_log(admin_user_id);
"""

ALL_TABLES: list[str] = [
    CREATE_USERS_TABLE,
    CREATE_USERS_UTM_MIGRATION,
    CREATE_REFRESH_TOKENS_TABLE,
    CREATE_BLACKLISTED_TOKENS_TABLE,
    CREATE_PASSWORD_RESET_TOKENS_TABLE,
    CREATE_EMAIL_VERIFICATION_TOKENS_TABLE,
    CREATE_USER_ROLE_TARIFF_HISTORY_TABLE,
    CREATE_GROUPS_TABLE,
    CREATE_GROUP_MEMBERS_TABLE,
    CREATE_GROUP_INVITES_TABLE,
    CREATE_PLAN_DEFINITIONS_TABLE,
    CREATE_BILLING_EVENTS_TABLE,
    CREATE_GROWTH_EVENTS_TABLE,
    CREATE_ADMIN_AUDIT_LOG_TABLE,
    CREATE_PROMO_CODES_TABLE,
    CREATE_BILLING_PLAN_REQUESTS_TABLE,
    CREATE_PROMO_CODE_REDEMPTIONS_TABLE,
    CREATE_INDEXES,
]

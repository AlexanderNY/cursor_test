-- Plan-change requests, invoices, promo codes (auth billing).

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

CREATE TABLE IF NOT EXISTS promo_code_redemptions (
    id SERIAL PRIMARY KEY,
    promo_code_id INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id INTEGER NULL REFERENCES billing_plan_requests(id) ON DELETE SET NULL,
    used_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (promo_code_id, user_id)
);

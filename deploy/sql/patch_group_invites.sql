-- Team invites: link/token for users who may not have an account yet
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

"""Scheduler service DDL."""

SCHEDULE_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_snapshots (
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_platform ON schedule_snapshots(platform);
"""

SCHEDULE_SNAPSHOTS_WP_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_snapshots_wp (
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_wp_user_id ON schedule_snapshots_wp(user_id);
"""

ALL_TABLES: list[str] = [
    SCHEDULE_SNAPSHOTS_TABLE,
    SCHEDULE_SNAPSHOTS_WP_TABLE,
]

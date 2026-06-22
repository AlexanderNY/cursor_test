"""SQL-определения таблиц Scheduler."""

SCHEDULE_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_snapshots (
    user_id INTEGER NOT NULL,
    platform VARCHAR(10) NOT NULL,
    publish_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    collect_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    schedule_type VARCHAR(20) NOT NULL DEFAULT 'immediate',
    time_intervals JSONB NOT NULL DEFAULT '[]',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
"""

SCHEDULE_SNAPSHOTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_platform ON schedule_snapshots(platform);
"""

SCHEDULE_SNAPSHOTS_WP_TABLE = """
CREATE TABLE IF NOT EXISTS schedule_snapshots_wp (
    user_id INTEGER NOT NULL,
    platform VARCHAR(10) NOT NULL,
    publish_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    collect_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    schedule_type VARCHAR(20) NOT NULL DEFAULT 'immediate',
    time_intervals JSONB NOT NULL DEFAULT '[]',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
"""

SCHEDULE_SNAPSHOTS_WP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_wp_user_id ON schedule_snapshots_wp(user_id);
"""

ALL_TABLES = [
    SCHEDULE_SNAPSHOTS_TABLE,
    SCHEDULE_SNAPSHOTS_INDEXES,
    SCHEDULE_SNAPSHOTS_WP_TABLE,
    SCHEDULE_SNAPSHOTS_WP_INDEX,
]

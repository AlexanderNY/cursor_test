"""DDL generators for post-like tables."""

from __future__ import annotations

from shared.db.post_columns import (
    POST_BASE_COLUMN_DEFS,
    POST_BASE_COLUMNS,
    POST_TENANCY_TABLES,
)


def build_add_column_if_missing(table_name: str, column_name: str, definition: str) -> str:
    """ALTER TABLE ADD COLUMN that is a no-op if the table or column already exists."""
    return (
        "DO $$ BEGIN\n"
        f"  ALTER TABLE {table_name} ADD COLUMN {column_name} {definition};\n"
        "EXCEPTION\n"
        "  WHEN duplicate_column THEN NULL;\n"
        "  WHEN undefined_table THEN NULL;\n"
        "END $$;"
    )


def build_post_tenancy_columns(table_name: str) -> str:
    """Add brand_id / channel_id to an existing post table (CREATE TABLE IF NOT EXISTS will not)."""
    return "\n".join(
        [
            build_add_column_if_missing(table_name, "brand_id", "INTEGER"),
            build_add_column_if_missing(table_name, "channel_id", "INTEGER"),
        ]
    )


def build_post_tenancy_migration(table_names: tuple[str, ...] | None = None) -> str:
    """Backfill tenancy columns on every post-like table that may already exist."""
    names = table_names or POST_TENANCY_TABLES
    return "\n".join(build_post_tenancy_columns(name) for name in names)


def build_post_table_ddl(
    table_name: str,
    *,
    extra_columns: dict[str, str] | None = None,
    column_overrides: dict[str, str] | None = None,
    table_constraints: list[str] | None = None,
    include_timestamps: bool = True,
) -> str:
    """Build CREATE TABLE IF NOT EXISTS for a platform or hub post table."""
    extra_columns = extra_columns or {}
    column_overrides = column_overrides or {}
    table_constraints = table_constraints or []

    column_lines: list[str] = ["    id SERIAL PRIMARY KEY"]

    for column_name in POST_BASE_COLUMNS:
        if column_name in extra_columns:
            continue
        definition = column_overrides.get(column_name, POST_BASE_COLUMN_DEFS[column_name])
        column_lines.append(f"    {column_name} {definition}")

    for column_name, definition in extra_columns.items():
        column_lines.append(f"    {column_name} {definition}")

    if include_timestamps:
        column_lines.extend(
            [
                "    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
                "    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
            ]
        )

    for constraint in table_constraints:
        column_lines.append(f"    {constraint}")

    body = ",\n".join(column_lines)
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n{body}\n);"


def build_post_indexes(
    table_name: str,
    *,
    with_publish_at: bool = False,
    with_user_domain: bool = False,
    with_source_unique: tuple[str, str] | None = None,
) -> str:
    """Standard indexes for post tables.

    Tenancy columns are added first: existing DBs were created before brand_id /
    channel_id existed, and CREATE TABLE IF NOT EXISTS does not add new columns.
    """
    statements = [
        build_post_tenancy_columns(table_name),
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_created ON {table_name}(user_id, created_at);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status_created ON {table_name}(status, created_at);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_brand_id ON {table_name}(brand_id) WHERE brand_id IS NOT NULL;",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_channel_id ON {table_name}(channel_id) WHERE channel_id IS NOT NULL;",
    ]
    if with_publish_at:
        statements.extend(
            [
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_publish_at ON {table_name}(publish_at);",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status_publish_at ON {table_name}(status, publish_at);",
            ]
        )
    if with_user_domain:
        statements.append(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_domain ON {table_name}(user_id, domain);"
        )
    if with_source_unique:
        col_a, col_b = with_source_unique
        statements.append(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_source "
            f"ON {table_name}({col_a}, {col_b}) WHERE {col_a} IS NOT NULL;"
        )
    return "\n".join(statements)

"""DDL generators for post-like tables."""

from __future__ import annotations

from shared.db.post_columns import POST_BASE_COLUMN_DEFS, POST_BASE_COLUMNS


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
    """Standard indexes for post tables."""
    statements = [
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_created ON {table_name}(user_id, created_at);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status_created ON {table_name}(status, created_at);",
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

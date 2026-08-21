"""Generate deploy/sql/init_schema.sql from shared schema modules."""

from __future__ import annotations

from pathlib import Path

from shared.db.registry import get_all_schemas


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "deploy" / "sql" / "init_schema.sql"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chunks = [
        "-- Greenfield PostgreSQL schema for db_bot (destroys existing public schema).",
        "DROP SCHEMA IF EXISTS public CASCADE;",
        "CREATE SCHEMA public;",
        "GRANT ALL ON SCHEMA public TO public;",
        "",
    ]
    for sql in get_all_schemas():
        chunks.append(sql.strip())
        chunks.append("")

    output_path.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

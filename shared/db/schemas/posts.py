"""Unified posts + post_targets DDL."""

from shared.db.post_model import (
    post_targets_indexes_sql,
    post_targets_table_ddl,
    posts_contract_cleanup_sql,
    posts_source_native_dedupe_sql,
    posts_unified_columns_sql,
)

POSTS_UNIFIED_MIGRATION = posts_unified_columns_sql()
POSTS_SOURCE_NATIVE_DEDUPE = posts_source_native_dedupe_sql()
POST_TARGETS_TABLE = post_targets_table_ddl()
POST_TARGETS_INDEXES = post_targets_indexes_sql()
POSTS_CONTRACT_CLEANUP = posts_contract_cleanup_sql()

ALL_TABLES: list[str] = [
    POSTS_UNIFIED_MIGRATION,
    POSTS_SOURCE_NATIVE_DEDUPE,
    POST_TARGETS_TABLE,
    POST_TARGETS_INDEXES,
    POSTS_CONTRACT_CLEANUP,
]

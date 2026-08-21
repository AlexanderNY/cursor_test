"""URL bot service DDL."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

URL_POSTS_TABLE = build_post_table_ddl("url_posts")
URL_POSTS_INDEXES = build_post_indexes("url_posts")

ALL_TABLES: list[str] = [
    URL_POSTS_TABLE,
    URL_POSTS_INDEXES,
]

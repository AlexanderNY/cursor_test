"""Redis key helper for tokens_valid_after."""

from shared.token_blacklist_redis import tokens_valid_after_key


def test_tokens_valid_after_key_format():
    assert tokens_valid_after_key(42) == "user:tokens_valid_after:42"

from services.bot_registry import resolve_game_bot_id, set_bot_mapping


def test_resolve_game_bot_id_uses_latest_mapping() -> None:
    set_bot_mapping({10: 1, 20: 2})
    assert resolve_game_bot_id(10) == 1
    assert resolve_game_bot_id(20) == 2
    assert resolve_game_bot_id(99) is None
    assert resolve_game_bot_id(None) is None

    set_bot_mapping({30: 3})
    assert resolve_game_bot_id(10) is None
    assert resolve_game_bot_id(30) == 3
    set_bot_mapping({})

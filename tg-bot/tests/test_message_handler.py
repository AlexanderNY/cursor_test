"""Tests for message_handler."""

from types import SimpleNamespace

from services.message_handler import MessageHandler


def _event(text: str):
    message = SimpleNamespace(message=text, media=None, id=1, date=None)
    return SimpleNamespace(
        raw_text=text,
        message=message,
        chat_id=-100123,
    )


def test_should_save_any_of():
    handler = MessageHandler()
    event = _event("hello world keyword test")
    assert handler.should_save_message(event, ["missing", "keyword"]) is True


def test_should_save_all_of():
    handler = MessageHandler()
    event = _event("alpha beta gamma")
    matched, conditions = handler.evaluate_conditions(
        event, ["alpha", "beta"], conditions_mode="all_of"
    )
    assert matched is True
    assert conditions == ["alpha", "beta"]


def test_all_of_fails_when_one_missing():
    handler = MessageHandler()
    event = _event("alpha only")
    matched, _ = handler.evaluate_conditions(event, ["alpha", "beta"], conditions_mode="all_of")
    assert matched is False


def test_regex_mode():
    handler = MessageHandler()
    event = _event("Price: $100")
    matched, _ = handler.evaluate_conditions(event, [r"\$\d+"], conditions_mode="regex")
    assert matched is True


def test_case_insensitive_any_of():
    handler = MessageHandler()
    event = _event("Внимание! срочно")
    matched, conditions = handler.evaluate_conditions(
        event, ["внимание"], conditions_mode="any_of"
    )
    assert matched is True
    assert conditions == ["внимание"]


def test_chat_id_in_list_strips_leading_minus():
    assert MessageHandler.chat_id_in_list(-1002142359467, ["1002142359467"]) is True
    assert MessageHandler.chat_id_in_list(-1002142359467, ["-1002142359467"]) is True
    assert MessageHandler.chat_id_in_list(-1002142359467, ["-100999"]) is False

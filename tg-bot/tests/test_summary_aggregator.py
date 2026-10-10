from shared.digest import should_create_digest


def test_should_create_digest_requires_text():
    assert should_create_digest([]) is False
    assert should_create_digest([{"post_text": "  "}]) is False
    assert should_create_digest([{"post_text": "hello"}]) is True
    assert should_create_digest([{"post_text": ""}, {"post_text": "x"}]) is True

"""Profile row mappers must not expose secrets."""

from services.profile_service import ProfileService


class _Col:
    def __init__(self, name: str):
        self.name = name


def _desc(names: list[str]):
    return [_Col(n) for n in names]


def test_tg_profile_masks_api_hash():
    svc = ProfileService()
    cols = ["user_id", "api_id", "api_hash", "auth_phone_code_hash", "time_intervals"]
    row = (1, "123", "secret-hash", "code-hash", "[]")
    profile = svc._row_to_tg_profile(row, _desc(cols))
    assert profile["api_hash"] == "***"
    assert profile["has_api_hash"] is True
    assert profile["auth_phone_code_hash"] == "***"


def test_tw_profile_drops_session_cookies():
    svc = ProfileService()
    cols = [
        "user_id",
        "twitter_oauth_access_token",
        "twitter_oauth_refresh_token",
        "twitter_password",
        "twitter_session_cookies",
        "time_intervals",
    ]
    row = (1, "at", "rt", "pw", '{"a":1}', "[]")
    profile = svc._row_to_tw_profile(row, _desc(cols))
    assert "twitter_session_cookies" not in profile
    assert profile["has_twitter_session"] is True
    assert profile["twitter_password"] == "***"


def test_wp_publish_masks_app_password():
    svc = ProfileService()
    cols = ["user_id", "app_password", "time_intervals", "site_url"]
    row = (1, "app-secret", None, "https://example.com")
    profile = svc._row_to_wp_publish_profile(row, _desc(cols))
    assert profile["app_password"] == "***"
    assert profile["has_app_password"] is True

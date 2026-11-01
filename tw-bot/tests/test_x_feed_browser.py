"""Юнит-тесты парсера ленты X (без живого x.com / Chrome)."""

from services.selenium_driver import user_agent_metadata
from services.x_feed_browser import (
    canonical_status_url,
    dumps_cookies,
    extract_status_id,
    following_tab_label_matches,
    loads_cookies,
    parse_tweet_card_fields,
)
from services.x_selenium_verify import (
    X_LOGIN_LIMITED_MESSAGE,
    is_extra_identity_prompt,
    is_x_browser_block,
    is_x_home_url,
    is_x_login_limited,
    is_x_login_url,
    login_form_alert_message,
    x_page_access_denied,
)


def test_extract_status_id_from_user_status_href():
    assert extract_status_id("https://x.com/elonmusk/status/1234567890") == "1234567890"
    assert extract_status_id("https://twitter.com/foo/status/99887766?s=20") == "99887766"


def test_extract_status_id_from_web_status():
    assert extract_status_id("https://x.com/i/web/status/555") == "555"
    assert extract_status_id("/i/web/status/555/") == "555"


def test_extract_status_id_rejects_non_status():
    assert extract_status_id("https://x.com/home") is None
    assert extract_status_id("") is None
    assert extract_status_id("https://x.com/user/status/") is None


def test_canonical_status_url():
    assert canonical_status_url("42") == "https://x.com/i/web/status/42"


def test_parse_tweet_card_fields_prefers_first_valid_href():
    card = parse_tweet_card_fields(
        [
            "https://x.com/alice",
            "https://x.com/alice/status/777888999",
            "https://x.com/alice/status/777888999/analytics",
        ],
        "Hello from the feed\n#line2",
    )
    assert card is not None
    assert card["status_id"] == "777888999"
    assert card["url"] == "https://x.com/i/web/status/777888999"
    assert card["text"] == "Hello from the feed\n#line2"


def test_parse_tweet_card_fields_none_without_status():
    assert parse_tweet_card_fields(["https://x.com/bob"], "no status link") is None


def test_user_and_web_status_same_canonical_id():
    a = extract_status_id("https://x.com/someone/status/111222333")
    b = extract_status_id("https://x.com/i/web/status/111222333")
    assert a == b == "111222333"
    assert canonical_status_url(a) == canonical_status_url(b)


def test_cookies_roundtrip():
    raw = [
        {
            "name": "auth_token",
            "value": "secret",
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "expiry": 1700000000.9,
        },
        {"name": "ct0", "value": "csrf", "domain": ".x.com", "path": "/"},
        {"bad": True},
    ]
    dumped = dumps_cookies(raw)
    loaded = loads_cookies(dumped)
    assert len(loaded) == 2
    assert loaded[0]["name"] == "auth_token"
    assert loaded[0]["value"] == "secret"
    assert loaded[1]["name"] == "ct0"


def test_loads_cookies_empty_or_invalid():
    assert loads_cookies(None) == []
    assert loads_cookies("") == []
    assert loads_cookies("not-json") == []
    assert loads_cookies("{}") == []


def test_following_tab_label_matches_chronological_names_only():
    assert following_tab_label_matches("Following")
    assert following_tab_label_matches("  Following\n")
    assert following_tab_label_matches("Подписки")
    assert following_tab_label_matches("Читаю")
    assert not following_tab_label_matches("For you")
    assert not following_tab_label_matches("Для вас")
    assert not following_tab_label_matches("Подписчики")
    assert not following_tab_label_matches("")


def test_home_url_is_path_not_login_query():
    assert is_x_home_url("https://x.com/home")
    assert is_x_home_url("https://x.com/home/")
    assert is_x_home_url("https://x.com/home?lang=en")
    assert is_x_home_url("https://twitter.com/home")
    assert is_x_home_url("https://www.x.com/home")
    login = "https://x.com/i/flow/login?redirect_after_login=%2Fhome"
    assert not is_x_home_url(login)
    assert is_x_login_url(login)
    assert is_x_login_url("https://x.com/i/flow/login")
    assert is_x_login_url("https://x.com/account/access")
    assert is_x_login_url(
        "https://x.com/i/jf/onboarding/web?redirect_after_login=%2Fhome&mode=login"
    )
    assert not is_x_login_url("https://x.com/home")
    assert not is_x_home_url("https://evil-x.com/home")
    assert not is_x_home_url("https://x.com/elonmusk")


def test_extra_identity_prompt_is_not_the_sign_in_heading():
    assert is_extra_identity_prompt("Enter your phone number or email address")
    assert is_extra_identity_prompt("Введите номер телефона или адрес электронной почты")
    assert not is_extra_identity_prompt("Sign in to X")
    assert not is_extra_identity_prompt("Enter your password")
    assert not is_extra_identity_prompt("Phone, email, or username")
    assert not is_extra_identity_prompt("")


def test_chrome_403_page_is_not_a_password_failure():
    assert x_page_access_denied(
        "https://x.com/home",
        "x.com",
        "Access to x.com was denied\nHTTP ERROR 403",
    )
    assert not x_page_access_denied(
        "https://x.com/i/jf/onboarding/web",
        "X",
        "Email or username",
    )
    assert is_x_browser_block("X отклонил браузер (HTTP 403), страница входа не открылась.")
    assert not is_x_browser_block("Неверный пароль")


def test_user_agent_metadata_is_a_normal_chrome():
    meta = user_agent_metadata("156.0.8078.73")
    brands = [item["brand"] for item in meta["brands"]]
    assert brands == ["Chromium", "Google Chrome", "Not.A/Brand"]
    assert all(item["version"] == "156" for item in meta["brands"][:2])
    assert meta["platform"] == "Linux"
    assert meta["mobile"] is False
    assert "HeadlessChrome" not in brands


def test_login_limit_alert_is_not_a_missing_password_field():
    alert = "We’ve temporarily limited your login. Please try again later."
    assert is_x_login_limited(alert)
    assert login_form_alert_message(alert) == X_LOGIN_LIMITED_MESSAGE
    assert is_x_login_limited(X_LOGIN_LIMITED_MESSAGE)
    assert login_form_alert_message("Did someone say … cookies?") is None
    assert login_form_alert_message("") is None

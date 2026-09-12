import importlib.util
from pathlib import Path

_HELPERS = Path(__file__).resolve().parents[1] / "services" / "vk_helpers.py"
_spec = importlib.util.spec_from_file_location("vk_helpers_under_test", _HELPERS)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

build_vk_callback_api_url = _mod.build_vk_callback_api_url
build_vk_oauth_redirect_uri = _mod.build_vk_oauth_redirect_uri
parse_vk_group_id = _mod.parse_vk_group_id


def test_oauth_redirect_strips_api_prefix():
    assert (
        build_vk_oauth_redirect_uri("https://www.copyparse.ru/api")
        == "https://www.copyparse.ru/vk/oauth/callback"
    )


def test_oauth_redirect_localhost_gateway_port():
    assert (
        build_vk_oauth_redirect_uri("http://localhost:8000")
        == "http://localhost:8000/vk/oauth/callback"
    )


def test_oauth_redirect_already_complete():
    uri = "https://www.copyparse.ru/vk/oauth/callback"
    assert build_vk_oauth_redirect_uri(uri) == uri
    assert build_vk_oauth_redirect_uri(uri + "/") == uri


def test_callback_api_url_strips_api_prefix():
    assert (
        build_vk_callback_api_url("https://www.copyparse.ru/api")
        == "https://www.copyparse.ru/vk/callback"
    )


def test_parse_club_group_id():
    assert parse_vk_group_id("club236672543") == 236672543
    assert parse_vk_group_id("-236672543") == 236672543

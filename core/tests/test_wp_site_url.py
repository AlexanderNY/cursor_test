"""WordPress site URL helpers for brand channels."""

import importlib.util
from pathlib import Path

_HELPERS = Path(__file__).resolve().parents[1] / "services" / "smm_networks.py"
_spec = importlib.util.spec_from_file_location("smm_networks_under_test", _HELPERS)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

normalize_wp_site_url = _mod.normalize_wp_site_url
wp_site_urls_match = _mod.wp_site_urls_match


def test_normalize_wp_site_url():
    assert normalize_wp_site_url("HTTPS://Example.COM/blog/") == "https://example.com/blog"
    assert normalize_wp_site_url("example.com") == "https://example.com"
    assert normalize_wp_site_url("http://127.0.0.1:8088/") == "http://127.0.0.1:8088"
    assert normalize_wp_site_url("") == ""
    assert normalize_wp_site_url(None) == ""


def test_wp_site_urls_match():
    assert wp_site_urls_match("https://Example.com/", "https://example.com")
    assert not wp_site_urls_match("https://a.com", "https://b.com")
    assert not wp_site_urls_match("", "")

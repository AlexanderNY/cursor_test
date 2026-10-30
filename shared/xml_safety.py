"""Reject XML documents that can expand into a huge tree."""

from __future__ import annotations


def assert_safe_xml(xml_text: str) -> None:
    """Refuse DTD and entity declarations before ElementTree parses the feed."""
    sample = (xml_text or "")[:65536].lower()
    if "<!doctype" in sample or "<!entity" in sample:
        raise ValueError("XML DTD is not allowed")

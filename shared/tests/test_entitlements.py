"""Правила грантов тарифа: ранг, 30 дней, выбор старшего доступа."""

from datetime import datetime

import pytest

from shared.billing.entitlements import (
    PAID_GRANT_DAYS,
    allows_paid_mark,
    grant_expires_at,
    normalize_promo_kind_fields,
    resolve_effective_tariff,
)


def test_paid_mark_allows_upgrade_and_same_tier_renewal():
    assert allows_paid_mark("free", "standard")
    assert allows_paid_mark("standard", "standard")
    assert allows_paid_mark("standard", "full")
    assert allows_paid_mark("full", "full")
    assert allows_paid_mark("basic", "standard")


def test_paid_mark_rejects_downgrade_and_free():
    assert not allows_paid_mark("full", "standard")
    assert not allows_paid_mark("standard", "free")
    assert not allows_paid_mark("free", "free")


def test_grant_lasts_30_days_after_mark():
    marked = datetime(2026, 1, 1, 15, 30)
    assert grant_expires_at(marked) == datetime(2026, 1, 31, 15, 30)
    assert PAID_GRANT_DAYS == 30


def test_higher_grant_wins_then_the_remaining_one():
    full_until = datetime(2026, 1, 10)
    standard_until = datetime(2026, 2, 1)
    grants = [
        {"tariff": "full", "status": "active", "expires_at": full_until, "source": "promo"},
        {"tariff": "standard", "status": "active", "expires_at": standard_until, "source": "payment"},
    ]
    tariff, expires_at = resolve_effective_tariff(grants)
    assert tariff == "full"
    assert expires_at == full_until

    tariff, expires_at = resolve_effective_tariff([grants[1]])
    assert tariff == "standard"
    assert expires_at == standard_until


def test_expired_and_empty_grants_fall_back_to_free():
    grants = [
        {"tariff": "full", "status": "expired", "expires_at": datetime(2026, 1, 1), "source": "payment"},
    ]
    assert resolve_effective_tariff(grants) == ("free", None)
    assert resolve_effective_tariff([]) == ("free", None)


def test_same_rank_keeps_the_later_expiry():
    early = datetime(2026, 3, 1)
    late = datetime(2026, 4, 1)
    tariff, expires_at = resolve_effective_tariff(
        [
            {"tariff": "standard", "status": "active", "expires_at": early, "source": "promo"},
            {"tariff": "standard", "status": "active", "expires_at": late, "source": "payment"},
        ]
    )
    assert tariff == "standard"
    assert expires_at == late


def test_grant_promo_requires_tariff_and_defaults_to_30_days():
    fields = normalize_promo_kind_fields({"kind": "grant", "applies_to_tariff": "full"})
    assert fields["kind"] == "grant"
    assert fields["applies_to_tariff"] == "full"
    assert fields["grant_days"] == 30
    assert fields["discount_percent"] is None


def test_grant_promo_rejects_missing_tariff():
    with pytest.raises(ValueError):
        normalize_promo_kind_fields({"kind": "grant"})


def test_discount_promo_still_needs_one_discount():
    fields = normalize_promo_kind_fields({"discount_percent": 20, "applies_to_tariff": "standard"})
    assert fields["kind"] == "discount"
    assert fields["discount_percent"] == 20
    assert fields["grant_days"] is None
    with pytest.raises(ValueError):
        normalize_promo_kind_fields({"kind": "discount"})

"""Tests for Stock DD domain models."""

from datetime import date

from stock_dd.models import (
    CompanyId,
    CompanyIdentity,
    CompanyListing,
)


def test_company_identity_uses_stable_internal_identifier() -> None:
    company_id = CompanyId("company-apple")

    identity = CompanyIdentity(
        company_id=company_id,
        legal_name="Apple Inc.",
        cik="0000320193",
        alternate_names=("Apple Computer, Inc.",),
    )

    assert identity.company_id == company_id
    assert identity.legal_name == "Apple Inc."
    assert identity.cik == "0000320193"
    assert identity.is_active is True
    assert identity.alternate_names == ("Apple Computer, Inc.",)


def test_company_identity_has_safe_defaults() -> None:
    identity = CompanyIdentity(
        company_id=CompanyId("company-example"),
        legal_name="Example Corporatino",
        cik="0000000001",
    )

    assert identity.is_active is True
    assert identity.alternate_names == ()


def test_company_listing_tracks_listing_history() -> None:
    listing = CompanyListing(
        company_id=CompanyId("company-example"),
        ticker="EXMP",
        exchange="NASDAQ",
        security_name="Class A Common Stock",
        valid_from=date(2020, 1, 2),
    )

    assert listing.ticker == "EXMP"
    assert listing.exchange == "NASDAQ"
    assert listing.security_name == "Class A Common Stock"
    assert listing.valid_from == date(2020, 1, 2)
    assert listing.valid_to is None
    assert listing.is_active is True

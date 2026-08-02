"""Tests for Stock DD domain models."""

from datetime import UTC, date, datetime

from stock_dd.models import (
    CompanyId,
    CompanyIdentity,
    CompanyListing,
    EvidenceCitation,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
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


def test_evidence_source_preserves_document_metadata() -> None:
    source_id = EvidenceSourceId("source-apple-2026-proxy")

    source = EvidenceSource(
        source_id=source_id,
        source_type=EvidenceSourceType.REGULATORY_FILING,
        title="Apple Inc. 2026 Proxy Statement",
        publisher="Apple Inc.",
        published_on=date(2026, 1, 9),
        retrieved_at=datetime(2026, 8, 2, 17, 15, tzinfo=UTC),
        url="https://www.sec.gov/example",
        external_id="0000320193-26-000006",
        filing_form="DEF 14A",
        raw_file_path=("data/raw/sec/0000320193/filings/0000320193-26-000006.html"),
        sha256="example-sha256",
    )

    assert source.source_id == source_id
    assert source.source_type is EvidenceSourceType.REGULATORY_FILING
    assert source.publisher == "Apple Inc."
    assert source.published_on == date(2026, 1, 9)
    assert source.external_id == "0000320193-26-000006"
    assert source.filing_form == "DEF 14A"
    assert source.language == "en"


def test_evidence_source_has_optional_metadata_defaults() -> None:
    source = EvidenceSource(
        source_id=EvidenceSourceId("source-example"),
        source_type=EvidenceSourceType.COMPANY_WEBPAGE,
        title="Executive Leadership",
        publisher="Example Corporation",
        retrieved_at=datetime(2026, 8, 2, 17, 15, tzinfo=UTC),
    )

    assert source.published_on is None
    assert source.url is None
    assert source.external_id is None
    assert source.filing_form is None
    assert source.raw_file_path is None
    assert source.sha256 is None
    assert source.language == "en"


def test_evidence_citation_reference_part_of_source() -> None:
    source_id = EvidenceSourceId("source-example")

    citation = EvidenceCitation(
        source_id=source_id,
        supporting_excerpt=(
            "Jane Smith has served as Chief Financial Officer since 2024."
        ),
        location="Leadership - Jane Smith",
    )

    assert citation.source_id == source_id
    assert citation.supporting_excerpt is not None
    assert citation.location == "Leadership - Jane Smith"

"""Tests for Stock DD domain models."""

from datetime import UTC, date, datetime

import pytest

from stock_dd.models import (
    CareerPosition,
    CareerPositionId,
    CompanyId,
    CompanyIdentity,
    CompanyListing,
    DatePrecision,
    EvidenceCitation,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
    Executive,
    ExecutiveId,
    ExecutiveRole,
    ExecutiveRoleId,
    ExecutiveRoleType,
    PartialDate,
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
        legal_name="Example Corporation",
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


def test_executive_preserves_identity_and_evidence() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-leadership"),
        supporting_excerpt=(
            "Jane Smith serves as the company's Chief Executive Officer."
        ),
        location="Executive Leadership — Jane Smith",
    )

    executive = Executive(
        executive_id=ExecutiveId("executive-jane-smith"),
        full_name="Jane Smith",
        alternate_names=("Jane A. Smith",),
        citations=(citation,),
    )

    assert executive.executive_id == ExecutiveId("executive-jane-smith")
    assert executive.full_name == "Jane Smith"
    assert executive.alternate_names == ("Jane A. Smith",)
    assert executive.citations == (citation,)


def test_executive_has_safe_alternate_name_default() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example"),
        location="Executive Officers",
    )

    executive = Executive(
        executive_id=ExecutiveId("executive-example"),
        full_name="Example Executive",
        citations=(citation,),
    )

    assert executive.alternate_names == ()
    assert executive.citations == (citation,)


def test_executive_ids_distinguish_people_with_the_same_name() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example"),
        location="Executive Officers",
    )

    first_executive = Executive(
        executive_id=ExecutiveId("executive-alex-kim-1"),
        full_name="Alex Kim",
        citations=(citation,),
    )
    second_executive = Executive(
        executive_id=ExecutiveId("executive-alex-kim-2"),
        full_name="Alex Kim",
        citations=(citation,),
    )

    assert first_executive.full_name == second_executive.full_name
    assert first_executive.executive_id != second_executive.executive_id


def test_partial_date_preserves_available_precision() -> None:
    year_only = PartialDate(year=2019)
    year_and_month = PartialDate(year=2011, month=8)
    complete_date = PartialDate(year=2025, month=3, day=1)

    assert year_only.precision is DatePrecision.YEAR
    assert year_only.month is None
    assert year_only.day is None

    assert year_and_month.precision is DatePrecision.MONTH
    assert year_and_month.month == 8
    assert year_and_month.day is None

    assert complete_date.precision is DatePrecision.DAY
    assert complete_date.month == 3
    assert complete_date.day == 1


def test_partial_date_rejects_day_wihtout_month() -> None:
    with pytest.raises(
        ValueError,
        match="month is required when day is provided",
    ):
        PartialDate(year=2024, day=1)


def test_partial_date_rejects_invalid_calendar_date() -> None:
    with pytest.raises(ValueError):
        PartialDate(year=2025, month=2, day=30)


def test_executive_role_connects_executive_to_company() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-appointment"),
        supporting_excerpt=(
            "Jane Smith was appointed Chief Executive Officer effective March 1, 2025."
        ),
        location="Executive appointment",
    )

    role = ExecutiveRole(
        role_id=ExecutiveRoleId("role-jane-smith-example-ceo"),
        company_id=CompanyId("company-example"),
        executive_id=ExecutiveId("executive-jane-smith"),
        role_type=ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER,
        reported_title="President and Chief Executive Officer",
        started_on=PartialDate(year=2025, month=3, day=1),
        appointment_announced_on=date(2025, 2, 10),
        citations=(citation,),
    )

    assert role.company_id == CompanyId("company-example")
    assert role.executive_id == ExecutiveId("executive-jane-smith")
    assert role.role_type is ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER
    assert role.reported_title == "President and Chief Executive Officer"
    assert role.started_on == PartialDate(year=2025, month=3, day=1)
    assert role.ended_on is None
    assert role.appointment_announced_on == date(2025, 2, 10)
    assert role.departure_announced_on is None
    assert role.is_interim is False
    assert role.citations == (citation,)


def test_executive_role_supports_partial_dates_and_interim_roles() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-interim-cfo"),
        location="Executive officers",
    )

    role = ExecutiveRole(
        role_id=ExecutiveRoleId("role-example-interim-cfo"),
        company_id=CompanyId("company-example"),
        executive_id=ExecutiveId("executive-example"),
        role_type=ExecutiveRoleType.CHIEF_FINANCIAL_OFFICER,
        reported_title="Interim Chief Financial Officer",
        started_on=PartialDate(year=2024, month=7),
        citations=(citation,),
        is_interim=True,
    )

    assert role.started_on == PartialDate(year=2024, month=7)
    assert role.started_on.precision is DatePrecision.MONTH
    assert role.is_interim is True


def test_career_position_preserves_employment_history() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-biography"),
        supporting_excerpt=(
            "Before joining the company, Jane Smith served as "
            "Chief Operating Officer of Example Corporation "
            "from 2019 to 2024."
        ),
        location="Executive biography = Jane Smith",
    )

    position = CareerPosition(
        position_id=CareerPositionId("career-jane-smith-example-corporation-coo"),
        executive_id=ExecutiveId("executive-jane-smith"),
        employer_company_id=CompanyId("company-example"),
        employer_name="Example Corporation",
        reported_title="Chief Operating Officer",
        started_on=PartialDate(year=2019),
        ended_on=PartialDate(year=2024),
        citations=(citation,),
    )

    assert position.position_id == CareerPositionId(
        "career-jane-smith-example-corporation-coo"
    )
    assert position.executive_id == ExecutiveId("executive-jane-smith")
    assert position.employer_company_id == CompanyId("company-example")
    assert position.employer_name == "Example Corporation"
    assert position.reported_title == "Chief Operating Officer"
    assert position.started_on == PartialDate(year=2019)
    assert position.ended_on == PartialDate(year=2024)
    assert position.citations == (citation,)


def test_career_position_supports_unresolved_employer() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-leadership-page"),
        location="Professional experience",
    )

    position = CareerPosition(
        position_id=CareerPositionId("career-example-private-company"),
        executive_id=ExecutiveId("executive-example"),
        employer_name="Private Technology Group",
        reported_title="Vice President of Finance",
        started_on=PartialDate(year=2020, month=6),
        citations=(citation,),
    )

    assert position.employer_company_id is None
    assert position.started_on == PartialDate(year=2020, month=6)
    assert position.started_on.precision is DatePrecision.MONTH
    assert position.ended_on is None


def test_career_position_ids_distinguish_roles_at_same_employer() -> None:
    citation = EvidenceCitation(
        source_id=EvidenceSourceId("source-example-biography"),
        location="Executive biography",
    )

    first_position = CareerPosition(
        position_id=CareerPositionId("career-example-vice-president"),
        executive_id=ExecutiveId("executive-example"),
        employer_name="Example Corporation",
        reported_title="Vice President",
        ended_on=PartialDate(year=2022),
        citations=(citation,),
    )

    second_position = CareerPosition(
        position_id=CareerPositionId("career-example-president"),
        executive_id=ExecutiveId("executive-example"),
        employer_name="Example Corporation",
        reported_title="President",
        ended_on=PartialDate(year=2022),
        citations=(citation,),
    )

    assert first_position.executive_id == second_position.executive_id
    assert first_position.employer_name == second_position.employer_name
    assert first_position.position_id != second_position.position_id

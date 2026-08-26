"""Integration tests for SQLite management-research persistence."""

from datetime import UTC, date, datetime
from pathlib import Path

from stock_dd.models import (
    CandidateClaimType,
    CandidateEvidence,
    CandidateEvidenceId,
    CandidateSubjectType,
    CareerPosition,
    CareerPositionId,
    CompanyEvent,
    CompanyEventId,
    CompanyEventType,
    CompanyId,
    CompanyIdentity,
    CompanyListing,
    CompanyListingId,
    EvidenceCitation,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
    Executive,
    ExecutiveId,
    ExecutiveRole,
    ExecutiveRoleId,
    ExecutiveRoleType,
    ExtractionMethod,
    PartialDate,
    VerificationStatus,
)
from stock_dd.repositories.sqlite import (
    SQLiteCandidateEvidenceRepository,
    SQLiteCareerPositionRepository,
    SQLiteCompanyEventRepository,
    SQLiteCompanyListingRepository,
    SQLiteCompanyRepository,
    SQLiteEvidenceSourceRepository,
    SQLiteExecutiveRepository,
    SQLiteExecutiveRoleRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def test_sqlite_research_graph_survives_transaction_and_reopen(
    sqlite_database_path: Path,
) -> None:
    company_id = CompanyId("company-example")
    listing_id = CompanyListingId("listing-example-nasdaq")
    source_id = EvidenceSourceId("source-example-nasdaq")
    executive_id = ExecutiveId("executive-jane-smith")
    role_id = ExecutiveRoleId("role-jane-smith-ceo")
    position_id = CareerPositionId("career-jane-smith-vp-finance")
    candidate_id = CandidateEvidenceId("candidate-jane-smith-ceo-start")
    event_id = CompanyEventId("event-jane-smith-appointed-ceo")

    company = CompanyIdentity(
        company_id=company_id,
        legal_name="Example Corporation",
        cik="0000000001",
        alternate_names=("Example Corp.",),
    )

    listing = CompanyListing(
        listing_id=listing_id,
        company_id=company_id,
        ticker="EXMP",
        exchange="NASDAQ",
        security_name="Example Corporation Common Stock",
        valid_from=date(2010, 1, 1),
    )

    source = EvidenceSource(
        source_id=source_id,
        source_type=EvidenceSourceType.REGULATORY_FILING,
        title="Example Corporation Form 8-K",
        publisher="U.S. Securities and Exchange Commission",
        retrieved_at=datetime(
            2026,
            8,
            26,
            16,
            30,
            tzinfo=UTC,
        ),
        published_on=date(2022, 6, 15),
        url="https://www.sec.gov/example",
        external_id="0000000001-22-000001",
        filing_form="8-K",
        raw_file_path="data/raw/sec/example-8k.html",
        sha256="a" * 64,
    )

    citation = EvidenceCitation(
        source_id=source_id,
        supporting_excerpt="Jane Smith was appointed Chief Executive Officer effective July 1, 2022",
        location="Item 5.02",
    )

    executive = Executive(
        executive_id=executive_id,
        full_name="Jane Smith",
        alternate_names=("Jane A. Smith",),
        citations=(citation,),
    )

    role = ExecutiveRole(
        role_id=role_id,
        company_id=company_id,
        executive_id=executive_id,
        role_type=ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER,
        reported_title="Chief Executive Officer",
        citations=(citation,),
        started_on=PartialDate(
            year=2022,
            month=7,
        ),
        appointment_announced_on=date(2022, 6, 15),
    )

    career_position = CareerPosition(
        position_id=position_id,
        executive_id=executive_id,
        employer_name="Example Corporation",
        reported_title="Vice President of Finace",
        citations=(citation,),
        employer_company_id=company_id,
        started_on=PartialDate(
            year=2018,
        ),
        ended_on=PartialDate(
            year=2022,
            month=6,
        ),
    )

    candidate = CandidateEvidence(
        candidate_id=candidate_id,
        subject_type=CandidateSubjectType.EXECUTIVE_ROLE,
        subject_name="Jane Smith - Chief Executive Officer",
        claim_type=CandidateClaimType.EXECUTIVE_ROLE_START_DATE,
        extracted_value=PartialDate(
            year=2022,
            month=7,
        ),
        citation=citation,
        extraction_method=ExtractionMethod.STRUCTURED_PARSER,
        extracted_at=datetime(
            2026,
            8,
            26,
            16,
            31,
            tzinfo=UTC,
        ),
        verification_status=VerificationStatus.PARSER_CONFIRMED,
        extraction_confidence=0.99,
        company_id=company_id,
        executive_id=executive_id,
    )

    event = CompanyEvent(
        event_id=event_id,
        company_id=company_id,
        event_type=CompanyEventType.EXECUTIVE_APPOINTMENT,
        description="Jane Smith was appointed Chief Executive Officer.",
        citations=(citation,),
        announced_on=date(2022, 6, 15),
        occurred_on=PartialDate(year=2022, month=7, day=1),
        related_executive_ids=(executive_id,),
        related_role_ids=(role_id,),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        company_repository = SQLiteCompanyRepository(connection)
        listing_repository = SQLiteCompanyListingRepository(connection)
        source_repository = SQLiteEvidenceSourceRepository(connection)
        executive_repository = SQLiteExecutiveRepository(connection)
        role_repository = SQLiteExecutiveRoleRepository(connection)
        career_repository = SQLiteCareerPositionRepository(connection)
        candidate_repository = SQLiteCandidateEvidenceRepository(connection)
        event_repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            company_repository.save(company)
            listing_repository.save(listing)
            source_repository.save(source)
            executive_repository.save(executive)
            role_repository.save(role)
            career_repository.save(career_position)
            candidate_repository.save(candidate)
            event_repository.save(event)

    with open_sqlite_database(sqlite_database_path) as connection:
        company_repository = SQLiteCompanyRepository(connection)
        listing_repository = SQLiteCompanyListingRepository(connection)
        source_repository = SQLiteEvidenceSourceRepository(connection)
        executive_repository = SQLiteExecutiveRepository(connection)
        role_repository = SQLiteExecutiveRoleRepository(connection)
        career_repository = SQLiteCareerPositionRepository(connection)
        candidate_repository = SQLiteCandidateEvidenceRepository(connection)
        event_repository = SQLiteCompanyEventRepository(connection)

        assert company_repository.get(company_id) == company
        assert listing_repository.get(listing_id) == listing
        assert source_repository.get(source_id) == source
        assert executive_repository.get(executive_id) == executive
        assert role_repository.get(role_id) == role
        assert career_repository.get(position_id) == career_position
        assert candidate_repository.get(candidate_id) == candidate
        assert event_repository.get(event_id) == event

        assert listing_repository.find_by_company(company_id) == (listing,)
        assert role_repository.find_by_executive(executive_id) == (role,)
        assert career_repository.find_by_employer_company(company_id) == (
            career_position,
        )
        assert candidate_repository.find_by_company(company_id) == (candidate,)
        assert event_repository.find_by_executive(executive_id) == (event,)
        assert event_repository.find_by_role(role_id) == (event,)

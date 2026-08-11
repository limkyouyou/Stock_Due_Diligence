"""Test for Stock DD repository contracts."""

from dataclasses import replace
from datetime import UTC, date, datetime

from stock_dd.models import (
    CandidateClaimType,
    CandidateEvidence,
    CandidateEvidenceId,
    CandidateSubjectType,
    CompanyId,
    CompanyIdentity,
    CompanyListing,
    EvidenceCitation,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
    ExecutiveId,
    ExtractionMethod,
    VerificationStatus,
)
from stock_dd.repositories import (
    CandidateEvidenceRepository,
    CompanyListingRepository,
    CompanyRepository,
    EvidenceSourceRepository,
)


class InMemoryCompanyRepository:
    """Small repository implementation used to test the contract."""

    def __init__(self) -> None:
        self._companies: dict[CompanyId, CompanyIdentity] = {}

    def save(self, company: CompanyIdentity) -> None:
        """Store a company by its internal identifer."""

        self._companies[company.company_id] = company

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        """Return a stored company by its internal identifier."""

        return self._companies.get(company_id)

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        """return the first stored company with the requested CIK."""

        return next(
            (company for company in self._companies.values() if company.cik == cik),
            None,
        )


class InMemoryEvidenceSourceRepository:
    """Small evidence-source repository used to test the contract."""

    def __init__(self) -> None:
        self._source: dict[EvidenceSourceId, EvidenceSource] = {}

    def save(self, source: EvidenceSource) -> None:
        """Store a source by its internal identifier."""

        self._source[source.source_id] = source

    def get(
        self,
        source_id: EvidenceSourceId,
    ) -> EvidenceSource | None:
        """Reutrn a stored source by its internal identifier."""

        return self._source.get(source_id)

    def find_by_external_id(
        self,
        external_id: str,
        *,
        source_type: EvidenceSourceType | None = None,
    ) -> tuple[EvidenceSource, ...]:
        """Return sources matching an external identifier."""

        return tuple(
            source
            for source in self._source.values()
            if source.external_id == external_id
            and (source_type is None or source.source_type is source_type)
        )


class InMemoryCandidateEvidenceRepository:
    """small candidate-evidence repository used to test the contract."""

    def __init__(self) -> None:
        self._candidates: dict[
            CandidateEvidenceId,
            CandidateEvidence,
        ] = {}

    def save(self, candidate: CandidateEvidence) -> None:
        """Store a candidate by its internal identifier."""

        self._candidates[candidate.candidate_id] = candidate

    def get(
        self,
        candidate_id: CandidateEvidenceId,
    ) -> CandidateEvidence | None:
        """Return a stored candidate by its internal identifier."""

        return self._candidates.get(candidate_id)

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Reurn candidate evidence associated with a company."""

        return tuple(
            candidate
            for candidate in self._candidates.values()
            if candidate.company_id == company_id
            and (
                verification_status is None
                or candidate.verification_status is verification_status
            )
        )

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidiate evidence associated with an executive."""

        return tuple(
            candidate
            for candidate in self._candidates.values()
            if candidate.executive_id == executive_id
            and (
                verification_status is None
                or candidate.verification_status is verification_status
            )
        )

    def find_by_status(
        self,
        verification_status: VerificationStatus,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence with a verification status."""

        return tuple(
            candidate
            for candidate in self._candidates.values()
            if candidate.verification_status is verification_status
        )


def test_company_repository_protocol_accepts_compatble_implementation() -> None:
    respository = InMemoryCompanyRepository()

    assert isinstance(respository, CompanyRepository)


def test_company_repository_supports_idenity_lookup() -> None:
    respository: CompanyRepository = InMemoryCompanyRepository()
    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )

    respository.save(company)

    assert respository.get(company.company_id) == company
    assert respository.find_by_cik("0000320193") == company


def test_company_repository_returns_none_for_missing_company() -> None:
    repository: CompanyRepository = InMemoryCompanyRepository()

    assert repository.get(CompanyId("company-missing")) is None
    assert repository.find_by_cik("0000000000") is None


class InMemoryCompanyListingRepository:
    """Small listing repository used to test the contract."""

    def __init__(self) -> None:
        self._listings: list[CompanyListing] = []

    def save(self, listing: CompanyListing) -> None:
        """Store or replace one listing record."""

        listing_key = (
            listing.company_id,
            listing.ticker.upper(),
            listing.exchange.upper(),
            listing.valid_from,
        )

        for index, existing in enumerate(self._listings):
            existing_key = (
                existing.company_id,
                existing.ticker.upper(),
                existing.exchange.upper(),
                existing.valid_from,
            )

            if existing_key == listing_key:
                self._listings[index] = listing
                return

        self._listings.append(listing)

    def find_by_ticker(
        self,
        ticker: str,
        *,
        as_of_date: date,
        exchange: str | None = None,
    ) -> tuple[CompanyListing, ...]:
        """Return listings matching the ticker and validity period."""

        normalized_ticker = ticker.upper()
        normalized_exchange = exchange.upper() if exchange else None

        return tuple(
            listing
            for listing in self._listings
            if listing.ticker.upper() == normalized_ticker
            and (
                normalized_exchange is None
                or listing.exchange.upper() == normalized_exchange
            )
            and (listing.valid_from is None or listing.valid_from <= as_of_date)
            and (listing.valid_to is None or as_of_date < listing.valid_to)
        )

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        """Return all listings belonging to a company."""

        return tuple(
            listing for listing in self._listings if listing.company_id == company_id
        )


def test_company_listing_repository_protocol_accepts_implementation() -> None:
    respository = InMemoryCompanyListingRepository()

    assert isinstance(respository, CompanyListingRepository)


def test_company_listing_repository_resolves_historical_ticker() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()

    historical_listing = CompanyListing(
        company_id=CompanyId("company-example"),
        ticker="OLD",
        exchange="NASDAQ",
        security_name="Common Stock",
        valid_from=date(2018, 1, 1),
        valid_to=date(2022, 12, 31),
        is_active=False,
    )
    current_listing = CompanyListing(
        company_id=CompanyId("company-example"),
        ticker="NEW",
        exchange="NASDAQ",
        security_name="Common Stock",
        valid_from=date(2023, 1, 1),
    )

    repository.save(historical_listing)
    repository.save(current_listing)

    assert repository.find_by_ticker(
        "old",
        as_of_date=date(2022, 6, 1),
    ) == (historical_listing,)

    assert repository.find_by_ticker("OLD", as_of_date=date(2024, 6, 1)) == ()


def test_company_listing_repository_can_filter_by_exchange() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()

    nasdaq_listing = CompanyListing(
        company_id=CompanyId("company-example-us"),
        ticker="EXMP",
        exchange="NASDAQ",
    )
    tsx_listing = CompanyListing(
        company_id=CompanyId("company-example-ca"),
        ticker="EXMP",
        exchange="TSX",
    )

    repository.save(nasdaq_listing)
    repository.save(tsx_listing)

    all_matches = repository.find_by_ticker(
        "EXMP",
        as_of_date=date(2026, 8, 2),
    )
    nasdaq_matches = repository.find_by_ticker(
        "EXMP",
        as_of_date=date(2026, 8, 2),
        exchange="nasdaq",
    )

    assert all_matches == (nasdaq_listing, tsx_listing)
    assert nasdaq_matches == (nasdaq_listing,)


def test_company_listing_repository_returns_company_listing_history() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()
    company_id = CompanyId("company-example")

    historical_listing = CompanyListing(
        company_id=company_id,
        ticker="OLD",
        exchange="NASDAQ",
        valid_to=date(2022, 12, 31),
        is_active=False,
    )
    current_listing = CompanyListing(
        company_id=company_id,
        ticker="NEW",
        exchange="NASDAQ",
        valid_from=date(2023, 1, 1),
    )

    repository.save(historical_listing)
    repository.save(current_listing)

    assert repository.find_by_company(company_id) == (
        historical_listing,
        current_listing,
    )
    assert repository.find_by_company(CompanyId("company-missing")) == ()


def _make_evidence_source(
    *,
    source_id: str = "source-example",
    external_id: str | None = None,
    source_type: EvidenceSourceType = (EvidenceSourceType.REGULATORY_FILING),
) -> EvidenceSource:
    return EvidenceSource(
        source_id=EvidenceSourceId(source_id),
        source_type=source_type,
        title="Example Research Source",
        publisher="Example Corporation",
        retrieved_at=datetime(2026, 8, 10, 20, 0, tzinfo=UTC),
        external_id=external_id,
    )


def test_evidence_source_repository_protocol_accepts_implementation() -> None:
    repository = InMemoryEvidenceSourceRepository()

    assert isinstance(repository, EvidenceSourceRepository)


def test_evidence_source_repository_supports_identity_lookup() -> None:
    repository: EvidenceSourceRepository = InMemoryEvidenceSourceRepository()
    source = _make_evidence_source()

    repository.save(source)

    assert repository.get(source.source_id) == source


def test_evidence_source_repository_returns_none_for_missing_source() -> None:
    repository: EvidenceSourceRepository = InMemoryEvidenceSourceRepository()

    assert repository.get(EvidenceSourceId("source-missing")) is None


def test_evidence_source_repository_finds_external_identifier() -> None:
    repository: EvidenceSourceRepository = InMemoryEvidenceSourceRepository()

    source = _make_evidence_source(
        source_id="source-example-filing",
        external_id="0000123456-26-000001",
    )

    repository.save(source)

    assert repository.find_by_external_id("0000123456-26-000001") == (source,)


def test_evidence_source_repository_can_filter_external_id_by_type() -> None:
    repository: EvidenceSourceRepository = InMemoryEvidenceSourceRepository()

    filing = _make_evidence_source(
        source_id="source-filing",
        external_id="external-123",
        source_type=EvidenceSourceType.REGULATORY_FILING,
    )
    regulator_data = _make_evidence_source(
        source_id="source-regulator-data",
        external_id="external-123",
        source_type=EvidenceSourceType.REGULATOR_DATA,
    )

    repository.save(filing)
    repository.save(regulator_data)

    assert repository.find_by_external_id("external-123") == (
        filing,
        regulator_data,
    )

    assert repository.find_by_external_id(
        "external-123",
        source_type=EvidenceSourceType.REGULATORY_FILING,
    ) == (filing,)


def test_evidence_source_repository_replaces_same_source_id() -> None:
    repository: EvidenceSourceRepository = InMemoryEvidenceSourceRepository()

    original = _make_evidence_source(
        source_id="source-example",
    )

    updated = EvidenceSource(
        source_id=original.source_id,
        source_type=original.source_type,
        title="Updated Source Tile",
        publisher=original.publisher,
        retrieved_at=original.retrieved_at,
    )

    repository.save(original)
    repository.save(updated)

    assert repository.get(original.source_id) == updated


def _make_candidate_evidence(
    *,
    candidate_id: str = "candidate-example",
    company_id: CompanyId | None = None,
    executive_id: ExecutiveId | None = None,
    verification_status: VerificationStatus = (VerificationStatus.UNREVIEWED),
) -> CandidateEvidence:
    if company_id is None:
        company_id = CompanyId("company-example")

    return CandidateEvidence(
        candidate_id=CandidateEvidenceId(candidate_id),
        subject_type=CandidateSubjectType.EXECUTIVE,
        subject_name="Jane Smith",
        claim_type=CandidateClaimType.EXECUTIVE_FULL_NAME,
        extracted_value="Jane Smith",
        citation=EvidenceCitation(
            source_id=EvidenceSourceId("source-example"),
            location="Executive officer",
        ),
        extraction_method=ExtractionMethod.RESEARCH_AGENT,
        extracted_at=datetime(
            2026,
            8,
            10,
            20,
            0,
            tzinfo=UTC,
        ),
        verification_status=verification_status,
        company_id=company_id,
        executive_id=executive_id,
    )


def test_candidate_evidence_repository_protocol_accepts_implementation() -> None:
    repository = InMemoryCandidateEvidenceRepository()

    assert isinstance(repository, CandidateEvidenceRepository)


def test_candidate_evidence_repository_supports_identify_lookup() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()
    candidate = _make_candidate_evidence()

    repository.save(candidate)

    assert repository.get(candidate.candidate_id) == candidate


def test_candidate_evidence_repository_returns_none_for_missing_candidate() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()

    assert repository.get(CandidateEvidenceId("candidate-missing")) is None


def test_candidate_evidence_repository_finds_candidates_by_company() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()

    first = _make_candidate_evidence(
        candidate_id="candidate-first",
    )
    second = _make_candidate_evidence(
        candidate_id="candidate-second",
    )
    other_company = _make_candidate_evidence(
        candidate_id="candidate-other-company",
        company_id=CompanyId("company-other"),
    )

    repository.save(first)
    repository.save(second)
    repository.save(other_company)

    assert repository.find_by_company(CompanyId("company-example")) == (
        first,
        second,
    )


def test_candidate_evidence_repository_filters_companyby_status() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()

    unreviwed = _make_candidate_evidence(
        candidate_id="candidate-unreviwed",
    )
    confirmed = _make_candidate_evidence(
        candidate_id="candidate-confirmed",
        verification_status=(VerificationStatus.PRIMARY_SOURCE_CONFIRMED),
    )

    repository.save(unreviwed)
    repository.save(confirmed)

    assert repository.find_by_company(
        CompanyId("company-example"),
        verification_status=VerificationStatus.UNREVIEWED,
    ) == (unreviwed,)


def test_candidate_evidence_repository_finds_candidates_by_executives() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()
    executive_id = ExecutiveId("executive-Jane-Smith")

    candidate = _make_candidate_evidence(
        executive_id=executive_id,
    )
    unresolved = _make_candidate_evidence(
        candidate_id="candidate-unresolved-executive",
    )

    repository.save(candidate)
    repository.save(unresolved)

    assert repository.find_by_executive(
        executive_id,
    ) == (candidate,)


def test_candidate_evidence_repository_finds_candidates_by_status() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()

    unreviewed = _make_candidate_evidence(
        candidate_id="candidate-unreviewed",
    )
    disputed = _make_candidate_evidence(
        candidate_id="candidate-disputed",
        verification_status=VerificationStatus.DISPUTED,
    )

    repository.save(unreviewed)
    repository.save(disputed)

    assert repository.find_by_status(VerificationStatus.DISPUTED) == (disputed,)


def test_candidate_evidence_repository_replaces_candidate_after_review() -> None:
    repository: CandidateEvidenceRepository = InMemoryCandidateEvidenceRepository()
    candidate = _make_candidate_evidence()

    confirmed = replace(
        candidate,
        verification_status=(VerificationStatus.PRIMARY_SOURCE_CONFIRMED),
    )

    repository.save(candidate)
    repository.save(confirmed)

    assert repository.get(candidate.candidate_id) == confirmed
    assert repository.find_by_status(VerificationStatus.UNREVIEWED) == ()
    assert repository.find_by_status(VerificationStatus.PRIMARY_SOURCE_CONFIRMED) == (
        confirmed,
    )

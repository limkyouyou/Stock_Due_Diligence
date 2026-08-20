"""Test for Stock DD repository contracts."""

from dataclasses import replace
from datetime import UTC, date, datetime

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
from stock_dd.repositories import (
    CandidateEvidenceRepository,
    CareerPositionRepository,
    CompanyEventRepository,
    CompanyListingRepository,
    CompanyRepository,
    EvidenceSourceRepository,
    ExecutiveRepository,
    ExecutiveRoleRepository,
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


class InMemoryExecutiveRepository:
    """Small executive repository used to test the contract."""

    def __init__(self) -> None:
        self._executives: dict[ExecutiveId, Executive] = {}

    def save(self, executive: Executive) -> None:
        """Store an executive by their internal identifier."""

        self._executives[executive.executive_id] = executive

    def get(
        self,
        executive_id: ExecutiveId,
    ) -> Executive | None:
        """Return a stored executive by their internal identifier."""

        return self._executives.get(executive_id)


class InMemoryCareerPositionRepository:
    """Small career-position repository used to test the contract."""

    def __init__(self) -> None:
        self._positions: dict[
            CareerPositionId,
            CareerPosition,
        ] = {}

    def save(self, position: CareerPosition) -> None:
        """Store a career position by it sinternal identifer."""

        self._positions[position.position_id] = position

    def get(
        self,
        position_id: CareerPositionId,
    ) -> CareerPosition | None:
        """Return a stored career position by its internal identifier."""

        return self._positions.get(position_id)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[CareerPosition, ...]:
        """Return career positions belonging to an executive."""

        return tuple(
            position
            for position in self._positions.values()
            if position.executive_id == executive_id
        )

    def find_by_employer_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CareerPosition, ...]:
        """Return positions linked to a known employer company."""

        return tuple(
            position
            for position in self._positions.values()
            if position.employer_company_id == company_id
        )


class InMemoryCompanyEventRepository:
    """Small company-event repository used to test the contract."""

    def __init__(self) -> None:
        self._events: dict[CompanyEventId, CompanyEvent] = {}

    def save(self, event: CompanyEvent) -> None:
        """Store an event by its internal identifier."""

        self._events[event.event_id] = event

    def get(
        self,
        event_id: CompanyEventId,
    ) -> CompanyEvent | None:
        """Return a stored event by its internal identifier."""

        return self._events.get(event_id)

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with a company."""

        return tuple(
            event
            for event in self._events.values()
            if event.company_id == company_id
            and (event_type is None or event.event_type is event_type)
        )

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """return events associated with an executive."""

        return tuple(
            event
            for event in self._events.values()
            if executive_id in event.related_executive_ids
            and (event_type is None or event.event_type is event_type)
        )

    def find_by_role(
        self,
        role_id: ExecutiveRoleId,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with an executive role."""

        return tuple(
            event
            for event in self._events.values()
            if role_id in event.related_role_ids
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
            and (listing.valid_to is None or as_of_date <= listing.valid_to)
        )

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        """Return all listings belonging to a company."""

        return tuple(
            listing for listing in self._listings if listing.company_id == company_id
        )


class InMemoryExecutiveRoleRepository:
    """Small executive-role repository used to test the contract."""

    def __init__(self) -> None:
        self._roles: dict[ExecutiveRoleId, ExecutiveRole] = {}

    def save(self, role: ExecutiveRole) -> None:
        """Store a role by its internal identifier."""

        self._roles[role.role_id] = role

    def get(self, role_id: ExecutiveRoleId) -> ExecutiveRole | None:
        """Return a stored role by its internal identifier."""

        return self._roles.get(role_id)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[ExecutiveRole, ...]:
        """Return all roles belonging to an executive."""

        return tuple(
            role for role in self._roles.values() if role.executive_id == executive_id
        )

    def find_by_company(
        self, company_id: CompanyId, *, role_type: ExecutiveRoleType | None = None
    ) -> tuple[ExecutiveRole, ...]:
        """Return roles associated with a company."""

        return tuple(
            role
            for role in self._roles.values()
            if (role.company_id == company_id)
            and (role_type is None or role.role_type is role_type)
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

    assert repository.find_by_ticker(
        "OLD",
        as_of_date=date(2022, 12, 31),
    ) == (historical_listing,)


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


def _make_executive(
    *,
    executive_id: str = "executive-jane-smith",
    full_name: str = "Jane Smith",
) -> Executive:
    return Executive(
        executive_id=ExecutiveId(executive_id),
        full_name=full_name,
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-example-executive-biography"),
                location="Executive officers",
            ),
        ),
    )


def test_executive_repository_protocol_accepts_implementation() -> None:
    respository: ExecutiveRepository = InMemoryExecutiveRepository()

    assert isinstance(respository, ExecutiveRepository)


def test_executive_repository_supports_identity_lookup() -> None:
    repository: ExecutiveRepository = InMemoryExecutiveRepository()
    executive = _make_executive()

    repository.save(executive)

    assert repository.get(executive.executive_id) == executive


def test_executive_repository_returns_none_for_missing_executive() -> None:
    repository: ExecutiveRepository = InMemoryExecutiveRepository()

    assert repository.get(ExecutiveId("executive-missing")) is None


def test_executive_repository_replaces_same_executive_id() -> None:
    repository: ExecutiveRepository = InMemoryExecutiveRepository()
    original = _make_executive()

    updated = replace(
        original,
        full_name="Jane A. Smith",
        alternate_names=("Jane Smith",),
    )

    repository.save(original)
    repository.save(updated)

    assert repository.get(original.executive_id) == updated


def _make_executive_role(
    *,
    role_id: str = "role-jane-smith-example-ceo",
    company_id: CompanyId | None = None,
    executive_id: ExecutiveId | None = None,
    role_type: ExecutiveRoleType = ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER,
) -> ExecutiveRole:
    if company_id is None:
        company_id = CompanyId("company-example")

    if executive_id is None:
        executive_id = ExecutiveId("executive-jane-smith")

    return ExecutiveRole(
        role_id=ExecutiveRoleId(role_id),
        company_id=company_id,
        executive_id=executive_id,
        role_type=role_type,
        reported_title="Chief Executive Officer",
        started_on=PartialDate(year=2022),
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-example-executive-role"),
                location="Executive officers",
            ),
        ),
    )


def test_executive_role_repository_protocol_accepts_implementation() -> None:
    repository = InMemoryExecutiveRoleRepository()

    assert isinstance(repository, ExecutiveRoleRepository)


def test_executive_role_repository_supports_identity_lookup() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()
    role = _make_executive_role()

    repository.save(role)

    assert repository.get(role.role_id) == role


def test_execuitve_role_repository_returns_none_for_missing_role() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()

    assert repository.get(ExecutiveRoleId("role-missing")) is None


def test_executive_role_repository_finds_roles_by_execuitve() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()

    ceo_role = _make_executive_role(
        role_id="role-jane-smith-ceo",
    )
    president_role = _make_executive_role(
        role_id="role-jane-smith-presitdent",
        role_type=ExecutiveRoleType.PRESIDENT,
    )
    other_executive_role = _make_executive_role(
        role_id="role-other-executive",
        executive_id=ExecutiveId("executive-other"),
    )

    repository.save(ceo_role)
    repository.save(president_role)
    repository.save(other_executive_role)

    assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
        ceo_role,
        president_role,
    )


def test_executive_role_repository_finds_roles_by_company() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()

    ceo_role = _make_executive_role(
        role_id="role-example-ceo",
    )
    cfo_role = _make_executive_role(
        role_id="role-example-cfo",
        executive_id=ExecutiveId("executive-cfo"),
        role_type=ExecutiveRoleType.CHIEF_FINANCIAL_OFFICER,
    )
    other_executive_role = _make_executive_role(
        role_id="role-other-company-ceo",
        company_id=CompanyId("company-other"),
    )

    repository.save(ceo_role)
    repository.save(cfo_role)
    repository.save(other_executive_role)

    assert repository.find_by_company(CompanyId("company-example")) == (
        ceo_role,
        cfo_role,
    )


def test_executive_role_repository_filters_company_by_role_type() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()

    ceo_role = _make_executive_role(
        role_id="role-example-ceo",
    )
    cfo_role = _make_executive_role(
        role_id="role-example-cfo",
        executive_id=ExecutiveId("executive-cfo"),
        role_type=ExecutiveRoleType.CHIEF_FINANCIAL_OFFICER,
    )

    repository.save(ceo_role)
    repository.save(cfo_role)

    assert repository.find_by_company(
        CompanyId("company-example"),
        role_type=ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER,
    ) == (ceo_role,)


def test_executive_role_repository_replaces_same_role_id() -> None:
    repository: ExecutiveRoleRepository = InMemoryExecutiveRoleRepository()
    original = _make_executive_role()

    updated = replace(
        original,
        reported_title="President and Chief Executive Officer",
    )

    repository.save(original)
    repository.save(updated)

    assert repository.get(original.role_id) == updated


def _make_career_position(
    *,
    position_id: str = "career-jane-smith-example=cfo",
    executive_id: str = "executive-jane-smith",
    employer_company_id: CompanyId | None = None,
    employer_name: str = "Example Corporation",
    reported_title: str = "Chief Financial Officer",
) -> CareerPosition:
    return CareerPosition(
        position_id=CareerPositionId(position_id),
        executive_id=ExecutiveId(executive_id),
        employer_company_id=employer_company_id,
        employer_name=employer_name,
        reported_title=reported_title,
        started_on=PartialDate(year=2018),
        ended_on=PartialDate(year=2022),
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-example-career-history"),
                location="Executive biograpy",
            ),
        ),
    )


def test_career_position_repository_protocol_accepts_implementation() -> None:
    repository = InMemoryCareerPositionRepository()

    assert isinstance(repository, CareerPositionRepository)


def test_career_position_repository_supports_identity_lookup() -> None:
    repository: CareerPositionRepository = InMemoryCareerPositionRepository()
    position = _make_career_position()

    repository.save(position)

    assert repository.get(position.position_id) == position


def test_career_position_repository_returns_none_for_missing_position() -> None:
    repository: CareerPositionRepository = InMemoryCareerPositionRepository()

    assert repository.get(CareerPositionId("career-missing")) is None


def test_career_position_repository_finds_positions_by_executive() -> None:
    repository: CareerPositionRepository = InMemoryCareerPositionRepository()

    first = _make_career_position(
        position_id="career-jane-smith-first",
    )
    second = _make_career_position(
        position_id="career-jane-smith-second",
        employer_name="Another Corporation",
        reported_title="Vice President of Finance",
    )
    other_executive = _make_career_position(
        position_id="career-other-executive",
        executive_id="executive-other",
    )

    repository.save(first)
    repository.save(second)
    repository.save(other_executive)

    assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
        first,
        second,
    )


def test_career_position_repository_finds_position_by_employer_company() -> None:
    repository: CareerPositionRepository = InMemoryCareerPositionRepository()

    company_id = CompanyId("company-example")

    matched = _make_career_position(
        position_id="career-matched-employer",
        employer_company_id=company_id,
    )

    unresolved = _make_career_position(
        position_id="career-unresolved-employer",
        employer_name="Example Corporation",
    )

    other_company = _make_career_position(
        position_id="career-other-company",
        employer_company_id=CompanyId("company-other"),
    )

    repository.save(matched)
    repository.save(unresolved)
    repository.save(other_company)

    assert repository.find_by_employer_company(
        company_id=CompanyId("company-example")
    ) == (matched,)


def test_career_position_repository_replaces_same_position_id() -> None:
    repository: CareerPositionRepository = InMemoryCareerPositionRepository()
    original = _make_career_position()

    updated = replace(
        original,
        reported_title="Senior Vice President and Chief Financial Officer",
    )

    repository.save(original)
    repository.save(updated)

    assert repository.get(original.position_id) == updated


def _make_company_event(
    *,
    event_id: str = "event-jane-smith-appointed",
    company_id: str = "company-example",
    executive_id: str = "executive-jane-smith",
    role_id: ExecutiveRoleId | None = None,
    event_type: CompanyEventType = (CompanyEventType.EXECUTIVE_APPOINTMENT),
) -> CompanyEvent:
    related_role_ids = (role_id,) if role_id is not None else ()

    return CompanyEvent(
        event_id=CompanyEventId(event_id),
        company_id=CompanyId(company_id),
        event_type=event_type,
        description="Jane Smith was appointed Chief Executive Officer.",
        announced_on=date(2022, 6, 15),
        occurred_on=PartialDate(year=2022, month=7, day=1),
        related_executive_ids=(ExecutiveId(executive_id),),
        related_role_ids=related_role_ids,
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-example-company-event"),
                location="Leadership announcement",
            ),
        ),
    )


def test_company_event_repository_protocol_accepts_implementation() -> None:
    repository = InMemoryCompanyEventRepository()

    assert isinstance(repository, CompanyEventRepository)


def test_company_event_repository_supports_identity_lookup() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()
    event = _make_company_event()

    repository.save(event)

    assert repository.get(event.event_id) == event


def test_company_event_repository_returns_none_for_missing_event() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    assert repository.get(CompanyEventId("event-missing")) is None


def test_company_event_repository_finds_events_by_company() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    appointment = _make_company_event(
        event_id="event-example-appointment",
    )

    departure = _make_company_event(
        event_id="event-example-departure",
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    )

    other_company = _make_company_event(
        event_id="event-other-company",
        company_id=CompanyId("company-other"),
    )

    repository.save(appointment)
    repository.save(departure)
    repository.save(other_company)

    assert repository.find_by_company(CompanyId("company-example")) == (
        appointment,
        departure,
    )


def test_company_event_reposiotry_filters_company_by_event_type() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    appointment = _make_company_event(
        event_id="event-example-appointment",
    )

    departure = _make_company_event(
        event_id="event-example-departure",
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    )

    repository.save(appointment)
    repository.save(departure)

    assert repository.find_by_company(
        CompanyId("company-example"),
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    ) == (departure,)


def test_company_event_repository_finds_events_by_executive() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    jane_event = _make_company_event()

    other_event = _make_company_event(
        event_id="event-other-executive",
        executive_id=ExecutiveId("executive-other"),
    )

    repository.save(jane_event)
    repository.save(other_event)

    assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
        jane_event,
    )


def test_company_event_repository_filters_executive_by_event_type() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    appointment = _make_company_event(
        event_id="event-example-appointment",
    )

    departure = _make_company_event(
        event_id="event-example-departure",
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    )

    repository.save(appointment)
    repository.save(departure)

    assert repository.find_by_executive(
        ExecutiveId("executive-jane-smith"),
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    ) == (departure,)


def test_company_event_repository_finds_events_by_role() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    role_id = ExecutiveRoleId("role-example-ceo")

    linked = _make_company_event(
        event_id="event-linked-role",
        role_id=role_id,
    )

    unlinked = _make_company_event(
        event_id="event-unlinked-role",
    )

    repository.save(linked)
    repository.save(unlinked)

    assert repository.find_by_role(role_id) == (linked,)


def test_company_event_repository_replaces_same_event_id() -> None:
    repository: CompanyEventRepository = InMemoryCompanyEventRepository()

    original = _make_company_event()

    updated = replace(
        original,
        description=("Jane Smith was appointed President and Chied Executive Officer."),
    )

    repository.save(original)
    repository.save(updated)

    assert repository.get(original.event_id) == updated

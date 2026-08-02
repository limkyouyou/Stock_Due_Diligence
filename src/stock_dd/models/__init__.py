"""Domain models for Stock DD MAS research data."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from stock_dd.models.company import AnnualFinancial as AnnualFinancial
from stock_dd.models.company import CompanyIdentity as CompanyIdentity
from stock_dd.models.company import CompanyListing as CompanyListing
from stock_dd.models.company import CompanyProfile as CompanyProfile
from stock_dd.models.company import CompanyResearchData as CompanyResearchData
from stock_dd.models.company import ResearchMetadata as ResearchMetadata
from stock_dd.models.dates import DatePrecision as DatePrecision
from stock_dd.models.dates import PartialDate as PartialDate
from stock_dd.models.identifiers import (
    CandidateEvidenceId as CandidateEvidenceId,
)
from stock_dd.models.identifiers import CareerPositionId as CareerPositionId
from stock_dd.models.identifiers import CompanyEventId as CompanyEventId
from stock_dd.models.identifiers import CompanyId as CompanyId
from stock_dd.models.identifiers import EvidenceSourceId as EvidenceSourceId
from stock_dd.models.identifiers import ExecutiveId as ExecutiveId
from stock_dd.models.identifiers import ExecutiveRoleId as ExecutiveRoleId


class EvidenceSourceType(StrEnum):
    """Supported categories of management-research evidence."""

    REGULATORY_FILING = "regulatory_filing"
    REGULATOR_DATA = "regulator_data"
    COMPANY_DOCUMENT = "company_document"
    COMPANY_WEBPAGE = "company_webpage"
    NEWS_ARTICLE = "news_article"
    INTERVIEW = "interview"
    PROFESSIONAL_PROFILE = "professional_profile"
    DISCOVERY_SOURCE = "discovery_source"
    OTHER = "other"


class ExecutiveRoleType(StrEnum):
    """Normalized categories for company executive roles."""

    CHIEF_EXECUTIVE_OFFICER = "chief_executive_officer"
    CHIEF_FINANCIAL_OFFICER = "chief_financial_officer"
    PRESIDENT = "president"
    CHIEF_OPERATING_OFFICER = "chief_operating_officer"
    EXECUTIVE_CHAIR = "executive_chair"
    OTHER_EXECUTIVE_OFFICER = "other_executive_officer"


class CandidateSubjectType(StrEnum):
    """Kinds of subjects that an extracted claim may describe."""

    COMPANY = "company"
    EXECUTIVE = "executive"
    EXECUTIVE_ROLE = "executive_role"
    CAREER_POSITION = "career_position"
    COMPANY_EVENT = "company_event"
    UNKNOWN = "unknown"


class CandidateClaimType(StrEnum):
    """Supported kinds of extracted management-research claims."""

    COMPANY_LEGAL_NAME = "company_legal_name"
    COMPANY_CIK = "company_cik"
    EXECUTIVE_FULL_NAME = "executive_full_name"
    EXECUTIVE_ALTERNATE_NAME = "executive_alternate_name"
    EXECUTIVE_ROLE_TITLE = "executive_role_title"
    EXECUTIVE_ROLE_START_DATE = "executive_role_start_date"
    EXECUTIVE_ROLE_END_DATE = "executive_role_end_date"
    CAREER_EMPLOYER = "career_employer"
    CAREER_TITLE = "career_title"
    CAREER_START_DATE = "career_start_date"
    CAREER_END_DATE = "career_end_date"
    EXECUTIVE_APPOINTMENT = "executive_appointment"
    EXECUTIVE_DEPARTURE = "executive_departure"
    OTHER = "other"


class ExtractionMethod(StrEnum):
    """Method used to extract a candidate research claim."""

    STRUCTURED_PARSER = "structured_parser"
    TEXT_PARSER = "text_parser"
    RESEARCH_AGENT = "research_agent"
    MANUAL_RESEARCH = "manual_research"


class VerificationStatus(StrEnum):
    """Current validation state of a candidate research claim."""

    UNREVIEWED = "unreviewed"
    PARSER_CONFIRMED = "parser_confirmed"
    PRIMARY_SOURCE_CONFIRMED = "primary_source_confirmed"
    MULTIPLE_SOURCE_CONFIRMED = "multiple_source_confirmed"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class CompanyEventType(StrEnum):
    """Supported categories of company events."""

    EXECUTIVE_APPOINTMENT = "executive_appointment"
    EXECUTIVE_DEPARTURE = "executive_departure"
    EXECUTIVE_ROLE_CHANGE = "executive_role_change"


type CandidateValue = str | int | float | bool | date | PartialDate


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceSource:
    """An external document or webpage used as research evidence."""

    source_id: EvidenceSourceId
    source_type: EvidenceSourceType
    title: str
    publisher: str
    retrieved_at: datetime
    published_on: date | None = None
    url: str | None = None
    external_id: str | None = None
    filing_form: str | None = None
    raw_file_path: str | None = None
    sha256: str | None = None
    language: str = "en"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceCitation:
    """A location within an evidence source supporting a research fact."""

    source_id: EvidenceSourceId
    supporting_excerpt: str | None = None
    location: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Executive:
    """A uniquely identified company executive."""

    executive_id: ExecutiveId
    full_name: str
    citations: tuple[EvidenceCitation, ...]
    alternate_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutiveRole:
    """An executive's leadership role at a company."""

    role_id: ExecutiveRoleId
    company_id: CompanyId
    executive_id: ExecutiveId
    role_type: ExecutiveRoleType
    reported_title: str
    citations: tuple[EvidenceCitation, ...]
    started_on: PartialDate | None = None
    ended_on: PartialDate | None = None
    appointment_announced_on: date | None = None
    departure_announced_on: date | None = None
    is_interim: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class CareerPosition:
    """A disclosed position in an executive's employment history."""

    position_id: CareerPositionId
    executive_id: ExecutiveId
    employer_name: str
    reported_title: str
    citations: tuple[EvidenceCitation, ...]
    employer_company_id: CompanyId | None = None
    started_on: PartialDate | None = None
    ended_on: PartialDate | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CompanyEvent:
    """A dated company occurrence supported by research evidence."""

    event_id: CompanyEventId
    company_id: CompanyId
    event_type: CompanyEventType
    description: str
    citations: tuple[EvidenceCitation, ...]
    announced_on: date | None = None
    occurred_on: PartialDate | None = None
    related_executive_ids: tuple[ExecutiveId, ...] = ()
    related_role_ids: tuple[ExecutiveRoleId, ...] = ()

    def __post_init__(self) -> None:
        """Ensure the event has enough temporal and subject information."""

        if self.announced_on is None and self.occurred_on is None:
            raise ValueError(
                "company event requires an announcement or occurrence date"
            )

        if not self.related_executive_ids:
            raise ValueError("executive company event requires a related executive")


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEvidence:
    """An extracted claim awaiting validation and normalization."""

    candidate_id: CandidateEvidenceId
    subject_type: CandidateSubjectType
    subject_name: str
    claim_type: CandidateClaimType
    extracted_value: CandidateValue
    citation: EvidenceCitation
    extraction_method: ExtractionMethod
    extracted_at: datetime
    verification_status: VerificationStatus = VerificationStatus.UNREVIEWED
    extraction_confidence: float | None = None
    company_id: CompanyId | None = None
    executive_id: ExecutiveId | None = None
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate confidence and rejection-state consistency."""

        if (
            self.extraction_confidence is not None
            and not 0.0 <= self.extraction_confidence <= 1.0
        ):
            raise ValueError("extraction confidence must be between 0.0 and 1.0")

        if (
            self.verification_status is VerificationStatus.REJECTED
            and not self.rejection_reason
        ):
            raise ValueError("rejection reason is required for rejected evidence")

        if (
            self.verification_status is not VerificationStatus.REJECTED
            and self.rejection_reason is not None
        ):
            raise ValueError("rejection reason is only valid for rejected evidence")

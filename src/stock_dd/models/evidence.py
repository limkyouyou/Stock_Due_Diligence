"""Evidence and extracted-claim domain models for Stock DD MAS."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from stock_dd.models.dates import PartialDate
from stock_dd.models.identifiers import (
    CandidateEvidenceId,
    CompanyId,
    EvidenceSourceId,
    ExecutiveId,
)


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

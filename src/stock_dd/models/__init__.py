"""Domain models for Stock DD MAS research data."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from stock_dd.models.company import AnnualFinancial as AnnualFinancial
from stock_dd.models.company import CompanyIdentity as CompanyIdentity
from stock_dd.models.company import CompanyListing as CompanyListing
from stock_dd.models.company import CompanyProfile as CompanyProfile
from stock_dd.models.company import CompanyResearchData as CompanyResearchData
from stock_dd.models.company import ResearchMetadata as ResearchMetadata
from stock_dd.models.dates import DatePrecision as DatePrecision
from stock_dd.models.dates import PartialDate as PartialDate
from stock_dd.models.evidence import CandidateClaimType as CandidateClaimType
from stock_dd.models.evidence import CandidateEvidence as CandidateEvidence
from stock_dd.models.evidence import CandidateSubjectType as CandidateSubjectType
from stock_dd.models.evidence import CandidateValue as CandidateValue
from stock_dd.models.evidence import EvidenceCitation as EvidenceCitation
from stock_dd.models.evidence import EvidenceSource as EvidenceSource
from stock_dd.models.evidence import EvidenceSourceType as EvidenceSourceType
from stock_dd.models.evidence import ExtractionMethod as ExtractionMethod
from stock_dd.models.evidence import VerificationStatus as VerificationStatus
from stock_dd.models.executives import CareerPosition as CareerPosition
from stock_dd.models.executives import Executive as Executive
from stock_dd.models.executives import ExecutiveRole as ExecutiveRole
from stock_dd.models.executives import ExecutiveRoleType as ExecutiveRoleType
from stock_dd.models.identifiers import (
    CandidateEvidenceId as CandidateEvidenceId,
)
from stock_dd.models.identifiers import CareerPositionId as CareerPositionId
from stock_dd.models.identifiers import CompanyEventId as CompanyEventId
from stock_dd.models.identifiers import CompanyId as CompanyId
from stock_dd.models.identifiers import EvidenceSourceId as EvidenceSourceId
from stock_dd.models.identifiers import ExecutiveId as ExecutiveId
from stock_dd.models.identifiers import ExecutiveRoleId as ExecutiveRoleId


class CompanyEventType(StrEnum):
    """Supported categories of company events."""

    EXECUTIVE_APPOINTMENT = "executive_appointment"
    EXECUTIVE_DEPARTURE = "executive_departure"
    EXECUTIVE_ROLE_CHANGE = "executive_role_change"


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

"""Executive and career-history domain models for Stock DD MAS."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from stock_dd.models.dates import PartialDate
from stock_dd.models.evidence import EvidenceCitation
from stock_dd.models.identifiers import (
    CareerPositionId,
    CompanyId,
    ExecutiveId,
    ExecutiveRoleId,
)


class ExecutiveRoleType(StrEnum):
    """Normalized categories for company executive roles."""

    CHIEF_EXECUTIVE_OFFICER = "chief_executive_officer"
    CHIEF_FINANCIAL_OFFICER = "chief_financial_officer"
    PRESIDENT = "president"
    CHIEF_OPERATING_OFFICER = "chief_operating_officer"
    EXECUTIVE_CHAIR = "executive_chair"
    OTHER_EXECUTIVE_OFFICER = "other_executive_officer"


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

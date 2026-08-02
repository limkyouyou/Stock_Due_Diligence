"""Company-event domain models for Stock DD MAS."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from stock_dd.models.dates import PartialDate
from stock_dd.models.evidence import EvidenceCitation
from stock_dd.models.identifiers import (
    CompanyEventId,
    CompanyId,
    ExecutiveId,
    ExecutiveRoleId,
)


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

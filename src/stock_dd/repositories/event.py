"""Repository contracts for company events."""

from typing import Protocol, runtime_checkable

from stock_dd.models import (
    CompanyEvent,
    CompanyEventId,
    CompanyEventType,
    CompanyId,
    ExecutiveId,
    ExecutiveRoleId,
)


@runtime_checkable
class CompanyEventRepository(Protocol):
    """Persistence contract for researched company event."""

    def save(self, event: CompanyEvent) -> None:
        """Persist a company event."""

        ...

    def get(
        self,
        event_id: CompanyEventId,
    ) -> CompanyEvent | None:
        """Return a company vent by its internal identifier."""

        ...

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with a company."""

        ...

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """Return event associated with an executive."""

        ...

    def find_by_role(
        self,
        role_id: ExecutiveRoleId,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with an executive role."""

        ...

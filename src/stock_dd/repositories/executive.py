"""Repository contracts for company executives."""

from typing import Protocol, runtime_checkable

from stock_dd.models import (
    CareerPosition,
    CareerPositionId,
    CompanyId,
    Executive,
    ExecutiveId,
    ExecutiveRole,
    ExecutiveRoleId,
    ExecutiveRoleType,
)


@runtime_checkable
class ExecutiveRepository(Protocol):
    """Persistence contract for executive identities."""

    def save(self, executive: Executive) -> None:
        """Persist an executive identity."""

        ...

    def get(
        self,
        executive_id: ExecutiveId,
    ) -> Executive | None:
        """Return an executive by their internal identifier."""

        ...


@runtime_checkable
class ExecutiveRoleRepository(Protocol):
    """Persistence contract for executive company roles."""

    def save(self, role: ExecutiveRole) -> None:
        """Persist an executive role."""

        ...

    def get(
        self,
        role_id: ExecutiveRoleId,
    ) -> ExecutiveRole | None:
        """Return an executive role by its internal identifier."""

        ...

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[ExecutiveRole, ...]:
        """Return all known roles for an executive."""

        ...

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        role_type: ExecutiveRoleType | None = None,
    ) -> tuple[ExecutiveRole, ...]:
        """Return executive roles associated with a company."""

        ...


@runtime_checkable
class CareerPositionRepository(Protocol):
    """Persistence contract for executive career positions."""

    def save(self, position: CareerPosition) -> None:
        """Persist an executive career position."""

        ...

    def get(
        self,
        position_id: CareerPositionId,
    ) -> CareerPosition | None:
        """Return a career positrion by its internal identifier."""

        ...

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[CareerPosition, ...]:
        """Return all known career positions for an executive."""

        ...

    def find_by_employer_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CareerPosition, ...]:
        """Return career positions linked to a known employer company."""

        ...

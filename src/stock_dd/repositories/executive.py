"""Repository contracts for company executives."""

from typing import Protocol, runtime_checkable

from stock_dd.models import (
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
        rold_id: ExecutiveRoleId,
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

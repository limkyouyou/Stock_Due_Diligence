"""Repository contracts for company research data."""

from typing import Protocol, runtime_checkable

from stock_dd.models import CompanyId, CompanyIdentity


@runtime_checkable
class CompanyRepository(Protocol):
    """Persistence contract for legal company identities."""

    def save(self, company: CompanyIdentity) -> None:
        """Persist a company identity."""

        ...

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        """Return a company by its internal identifier."""

        ...

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        """Return a company by its SEC Central Index Key."""

        ...

"""Repository contracts for company security listings."""

from datetime import date
from typing import Protocol, runtime_checkable

from stock_dd.models import (
    CompanyId,
    CompanyListing,
    CompanyListingId,
)


@runtime_checkable
class CompanyListingRepository(Protocol):
    """Persistence contract for publicly traded company listings."""

    def save(self, listing: CompanyListing) -> None:
        """Persist a company listing."""

        ...

    def get(
        self,
        listing_id: CompanyListingId,
    ) -> CompanyListing | None:
        """Return a company listing by its internal identifier."""

        ...

    def find_by_ticker(
        self,
        ticker: str,
        *,
        as_of_date: date,
        exchange: str | None = None,
    ) -> tuple[CompanyListing, ...]:
        """Return listings valid for a ticker on a particular date."""

        ...

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        """Return all known listings associated with a company."""

        ...

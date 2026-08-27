"""Application service for truested company-identity ingestion."""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from stock_dd.collectors import (
    CollectedCompanyIdentity,
    CompanyIdentityDataset,
)
from stock_dd.exceptions import NormalizationError
from stock_dd.models import (
    CompanyId,
    CompanyIdentity,
    CompanyListing,
    CompanyListingId,
)
from stock_dd.repositories import (
    CompanyListingRepository,
    CompanyRepository,
)


def _new_company_id() -> CompanyId:
    """Create a new internal company identifier."""

    return CompanyId(f"company-{uuid4()}")


def _new_listing_id() -> CompanyListingId:
    """Create a new internal company-listing identifier."""

    return CompanyListingId(f"listing-{uuid4()}")


@dataclass(frozen=True, slots=True, kw_only=True)
class CompanyIdentityIngestionResult:
    """Trusted records produced by company-identity ingestions."""

    company: CompanyIdentity
    listing: CompanyListing | None
    company_created: bool
    listing_created: bool


class CompanyIdentityIngestionService:
    """Promote collected company identity into trusted records."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        listing_repository: CompanyListingRepository,
        *,
        company_id_factory: Callable[[], CompanyId] = _new_company_id,
        listing_id_factory: Callable[[], CompanyListingId] = _new_listing_id,
    ) -> None:
        self._company_repository = company_repository
        self._listing_repository = listing_repository
        self._company_id_factory = company_id_factory
        self._listing_id_factory = listing_id_factory

    def ingest(
        self,
        dataset: CompanyIdentityDataset,
    ) -> CompanyIdentityIngestionResult:
        """Promote one unambiguous collected identity into trusted records."""

        match = self._require_single_match(dataset)

        company, company_created = self._resolve_company(match)
        listing, listing_created = self._resolve_listing(
            company,
            match,
        )

        self._company_repository.save(company)

        if listing_created and listing is not None:
            self._listing_repository.save(listing)

        return CompanyIdentityIngestionResult(
            company=company,
            listing=listing,
            company_created=company_created,
            listing_created=listing_created,
        )

    @staticmethod
    def _require_single_match(
        dataset: CompanyIdentityDataset,
    ) -> CollectedCompanyIdentity:
        """Return one unambiguous identity match."""

        if not dataset.matches:
            raise NormalizationError(
                f"Company identity collection returned no matches for ticker '{dataset.requested_ticker}'."
            )

        if len(dataset.matches) > 1:
            raise NormalizationError(
                f"Company identity collection returned multiple matches for ticker '{dataset.requested_ticker}'."
            )

        match = dataset.matches[0]

        if match.ticker.upper() != dataset.requested_ticker.upper():
            raise NormalizationError(
                "Collected company identity ticker does not match the requested ticker."
            )

        return match

    def _resolve_company(
        self,
        match: CollectedCompanyIdentity,
    ) -> tuple[CompanyIdentity, bool]:
        """Resolve or create the trusted company identity."""

        existing = self._company_repository.find_by_cik(match.cik)

        if existing is None:
            return (
                CompanyIdentity(
                    company_id=self._company_id_factory(),
                    legal_name=match.legal_name,
                    cik=match.cik,
                ),
                True,
            )

        if existing.legal_name != match.legal_name:
            raise NormalizationError(
                f"Collected company legal name conflicts with the trusted company stored for CIK '{match.cik}'."
            )

        return existing, False

    def _resolve_listing(
        self,
        company: CompanyIdentity,
        match: CollectedCompanyIdentity,
    ) -> tuple[CompanyListing | None, bool]:
        """Resolve or create a listing for the collected identity."""

        if match.exchange is None:
            return None, False

        existing_listings = self._listing_repository.find_by_company(company.company_id)

        matches = tuple(
            listing
            for listing in existing_listings
            if listing.ticker.upper() == match.ticker.upper()
            and listing.exchange.upper() == match.exchange.upper()
        )

        if len(matches) > 1:
            raise NormalizationError(
                f"Trusted company data contains multiple matching listings for ticker '{match.ticker}' on '{match.exchange}'."
            )

        if matches:
            return matches[0], False

        return (
            CompanyListing(
                listing_id=self._listing_id_factory(),
                company_id=company.company_id,
                ticker=match.ticker,
                exchange=match.exchange,
            ),
            True,
        )

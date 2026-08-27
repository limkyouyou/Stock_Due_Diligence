"""Tests for company-identity ingestion."""

from datetime import UTC, date, datetime

import pytest

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
from stock_dd.services import CompanyIdentityIngestionService


class InMemoryCompanyRepository:
    """Small company repository for service tests."""

    def __init__(self) -> None:
        self.companies: dict[CompanyId, CompanyIdentity] = {}

    def save(self, company: CompanyIdentity) -> None:
        self.companies[company.company_id] = company

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        return self.companies.get(company_id)

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        return next(
            (company for company in self.companies.values() if company.cik == cik),
            None,
        )


class InMemoryCompanyListingRepository:
    """Small listing repository for service tests."""

    def __init__(self) -> None:
        self.listings: dict[CompanyListingId, CompanyListing] = {}

    def save(self, listing: CompanyListing) -> None:
        self.listings[listing.listing_id] = listing

    def get(
        self,
        listing_id: CompanyListingId,
    ) -> CompanyListing | None:
        return self.listings.get(listing_id)

    def find_by_ticker(
        self,
        ticker: str,
        *,
        as_of_date: date,
        exchange: str | None = None,
    ) -> tuple[CompanyListing, ...]:
        return tuple(
            listing
            for listing in self.listings.values()
            if listing.ticker.upper() == ticker.upper()
            and (exchange is None or listing.exchange.upper() == exchange.upper())
            and (listing.valid_from is None or listing.valid_from <= as_of_date)
            and (listing.valid_to is None or as_of_date <= listing.valid_to)
        )

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        return tuple(
            listing
            for listing in self.listings.values()
            if listing.company_id == company_id
        )


def _make_dataset(
    *,
    legal_name: str = "Apple Inc.",
    cik: str = "0000320193",
    ticker: str = "AAPL",
    exchange: str | None = "Nasdaq",
) -> CompanyIdentityDataset:
    return CompanyIdentityDataset(
        provider="sec",
        requested_ticker=ticker,
        collected_at=datetime(
            2026,
            8,
            27,
            18,
            0,
            tzinfo=UTC,
        ),
        matches=(
            CollectedCompanyIdentity(
                legal_name=legal_name,
                cik=cik,
                ticker=ticker,
                exchange=exchange,
            ),
        ),
    )


def test_ingest_creates_company_and_listing() -> None:
    company_repository: CompanyRepository = InMemoryCompanyRepository()
    listing_repository: CompanyListingRepository = InMemoryCompanyListingRepository()

    service = CompanyIdentityIngestionService(
        company_repository,
        listing_repository,
        company_id_factory=lambda: CompanyId("company-apple"),
        listing_id_factory=lambda: CompanyListingId("listing-apple-nasdaq"),
    )

    result = service.ingest(_make_dataset())

    assert result.company == CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )
    assert result.listing == CompanyListing(
        listing_id=CompanyListingId("listing-apple-nasdaq"),
        company_id=CompanyId("company-apple"),
        ticker="AAPL",
        exchange="Nasdaq",
    )
    assert result.company_created is True
    assert result.listing_created is True

    assert company_repository.get(CompanyId("company-apple")) == result.company
    assert (
        listing_repository.get(CompanyListingId("listing-apple-nasdaq"))
        == result.listing
    )


def test_ingest_reuses_existing_company_and_listing() -> None:
    company_repository = InMemoryCompanyRepository()
    listing_repository = InMemoryCompanyListingRepository()

    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )
    listing = CompanyListing(
        listing_id=CompanyListingId("listing-apple"),
        company_id=company.company_id,
        ticker="AAPL",
        exchange="Nasdaq",
        security_name="Common Stock",
    )

    company_repository.save(company)
    listing_repository.save(listing)

    service = CompanyIdentityIngestionService(
        company_repository,
        listing_repository,
    )

    result = service.ingest(_make_dataset())

    assert result.company == company
    assert result.listing == listing
    assert result.company_created is False
    assert result.listing_created is False


def test_ingest_rejects_missing_match() -> None:
    service = CompanyIdentityIngestionService(
        InMemoryCompanyRepository(),
        InMemoryCompanyListingRepository(),
    )
    dataset = CompanyIdentityDataset(
        provider="sec",
        requested_ticker="UNKNOWN",
        collected_at=datetime(
            2026,
            8,
            27,
            18,
            0,
            tzinfo=UTC,
        ),
        matches=(),
    )

    with pytest.raises(
        NormalizationError,
        match="returned no matches",
    ):
        service.ingest(dataset)


def test_ingest_rejects_multiple_matches() -> None:
    service = CompanyIdentityIngestionService(
        InMemoryCompanyRepository(),
        InMemoryCompanyListingRepository(),
    )

    dataset = CompanyIdentityDataset(
        provider="sec",
        requested_ticker="DUP",
        collected_at=datetime(
            2026,
            8,
            27,
            18,
            0,
            tzinfo=UTC,
        ),
        matches=(
            CollectedCompanyIdentity(
                legal_name="Example One",
                cik="0000000001",
                ticker="DUP",
                exchange="NYSE",
            ),
            CollectedCompanyIdentity(
                legal_name="Example Two",
                cik="0000000002",
                ticker="DUP",
                exchange="Nasdaq",
            ),
        ),
    )

    with pytest.raises(
        NormalizationError,
        match="returned multiple matches",
    ):
        service.ingest(dataset)


def test_ingest_rejects_conflicting_legal_name() -> None:
    company_repository = InMemoryCompanyRepository()
    listing_repository = InMemoryCompanyListingRepository()

    company_repository.save(
        CompanyIdentity(
            company_id=CompanyId("company-apple"),
            legal_name="Different Legal Name",
            cik="0000320193",
        )
    )

    service = CompanyIdentityIngestionService(
        company_repository,
        listing_repository,
    )

    with pytest.raises(
        NormalizationError,
        match="legal name conflicts",
    ):
        service.ingest(_make_dataset())


def test_ingest_can_create_company_without_listing() -> None:
    company_repository = InMemoryCompanyRepository()
    listing_repository = InMemoryCompanyListingRepository()

    service = CompanyIdentityIngestionService(
        company_repository,
        listing_repository,
        company_id_factory=lambda: CompanyId("company-example"),
    )

    result = service.ingest(
        _make_dataset(
            legal_name="Example Corporation",
            cik="0000000001",
            ticker="EXMP",
            exchange=None,
        )
    )

    assert result.company.company_id == CompanyId("company-example")
    assert result.listing is None
    assert result.company_created is True
    assert result.listing_created is False
    assert listing_repository.listings == {}


def test_ingest_rejects_match_for_different_ticker() -> None:
    service = CompanyIdentityIngestionService(
        InMemoryCompanyRepository(),
        InMemoryCompanyListingRepository(),
    )

    dataset = CompanyIdentityDataset(
        provider="sec",
        requested_ticker="AAPL",
        collected_at=datetime(
            2026,
            8,
            27,
            18,
            0,
            tzinfo=UTC,
        ),
        matches=(
            CollectedCompanyIdentity(
                legal_name="Microsoft Corporation",
                cik="0000789019",
                ticker="MSFT",
                exchange="Nasdaq",
            ),
        ),
    )

    with pytest.raises(
        NormalizationError,
        match="does not match",
    ):
        service.ingest(dataset)

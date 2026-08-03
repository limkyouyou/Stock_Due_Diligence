"""Test for Stock DD repository contracts."""

from datetime import date

from stock_dd.models import CompanyId, CompanyIdentity, CompanyListing
from stock_dd.repositories import (
    CompanyListingRepository,
    CompanyRepository,
)


class InMemoryCompanyRepository:
    """Small repository implementation used to test the contract."""

    def __init__(self) -> None:
        self._companies: dict[CompanyId, CompanyIdentity] = {}

    def save(self, company: CompanyIdentity) -> None:
        """Store a company by its internal identifer."""

        self._companies[company.company_id] = company

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        """Return a stored company by its internal identifier."""

        return self._companies.get(company_id)

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        """return the first stored company with the requested CIK."""

        return next(
            (company for company in self._companies.values() if company.cik == cik),
            None,
        )


def test_company_repository_protocol_accepts_compatble_implementation() -> None:
    respository = InMemoryCompanyRepository()

    assert isinstance(respository, CompanyRepository)


def test_company_repository_supports_idenity_lookup() -> None:
    respository: CompanyRepository = InMemoryCompanyRepository()
    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )

    respository.save(company)

    assert respository.get(company.company_id) == company
    assert respository.find_by_cik("0000320193") == company


def test_company_repository_returns_none_for_missing_company() -> None:
    repository: CompanyRepository = InMemoryCompanyRepository()

    assert repository.get(CompanyId("company-missing")) is None
    assert repository.find_by_cik("0000000000") is None


class InMemoryCompanyListingRepository:
    """Small listing repository used to test the contract."""

    def __init__(self) -> None:
        self._listings: list[CompanyListing] = []

    def save(self, listing: CompanyListing) -> None:
        """Store or replace one listing record."""

        listing_key = (
            listing.company_id,
            listing.ticker.upper(),
            listing.exchange.upper(),
            listing.valid_from,
        )

        for index, existing in enumerate(self._listings):
            existing_key = (
                existing.company_id,
                existing.ticker.upper(),
                existing.exchange.upper(),
                existing.valid_from,
            )

            if existing_key == listing_key:
                self._listings[index] = listing
                return

        self._listings.append(listing)

    def find_by_ticker(
        self,
        ticker: str,
        *,
        as_of_date: date,
        exchange: str | None = None,
    ) -> tuple[CompanyListing, ...]:
        """Return listings matching the ticker and validity period."""

        normalized_ticker = ticker.upper()
        normalized_exchange = exchange.upper() if exchange else None

        return tuple(
            listing
            for listing in self._listings
            if listing.ticker.upper() == normalized_ticker
            and (
                normalized_exchange is None
                or listing.exchange.upper() == normalized_exchange
            )
            and (listing.valid_from is None or listing.valid_from <= as_of_date)
            and (listing.valid_to is None or as_of_date < listing.valid_to)
        )

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        """Return all listings belonging to a company."""

        return tuple(
            listing for listing in self._listings if listing.company_id == company_id
        )


def test_company_listing_repository_protocol_accepts_implementation() -> None:
    respository = InMemoryCompanyListingRepository()

    assert isinstance(respository, CompanyListingRepository)


def test_company_listing_repository_resolves_historical_ticker() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()

    historical_listing = CompanyListing(
        company_id=CompanyId("company-example"),
        ticker="OLD",
        exchange="NASDAQ",
        security_name="Common Stock",
        valid_from=date(2018, 1, 1),
        valid_to=date(2022, 12, 31),
        is_active=False,
    )
    current_listing = CompanyListing(
        company_id=CompanyId("company-example"),
        ticker="NEW",
        exchange="NASDAQ",
        security_name="Common Stock",
        valid_from=date(2023, 1, 1),
    )

    repository.save(historical_listing)
    repository.save(current_listing)

    assert repository.find_by_ticker(
        "old",
        as_of_date=date(2022, 6, 1),
    ) == (historical_listing,)

    assert repository.find_by_ticker("OLD", as_of_date=date(2024, 6, 1)) == ()


def test_company_listing_repository_can_filter_by_exchange() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()

    nasdaq_listing = CompanyListing(
        company_id=CompanyId("company-example-us"),
        ticker="EXMP",
        exchange="NASDAQ",
    )
    tsx_listing = CompanyListing(
        company_id=CompanyId("company-example-ca"),
        ticker="EXMP",
        exchange="TSX",
    )

    repository.save(nasdaq_listing)
    repository.save(tsx_listing)

    all_matches = repository.find_by_ticker(
        "EXMP",
        as_of_date=date(2026, 8, 2),
    )
    nasdaq_matches = repository.find_by_ticker(
        "EXMP",
        as_of_date=date(2026, 8, 2),
        exchange="nasdaq",
    )

    assert all_matches == (nasdaq_listing, tsx_listing)
    assert nasdaq_matches == (nasdaq_listing,)


def test_company_listing_repository_returns_company_listing_history() -> None:
    repository: CompanyListingRepository = InMemoryCompanyListingRepository()
    company_id = CompanyId("company-example")

    historical_listing = CompanyListing(
        company_id=company_id,
        ticker="OLD",
        exchange="NASDAQ",
        valid_to=date(2022, 12, 31),
        is_active=False,
    )
    current_listing = CompanyListing(
        company_id=company_id,
        ticker="NEW",
        exchange="NASDAQ",
        valid_from=date(2023, 1, 1),
    )

    repository.save(historical_listing)
    repository.save(current_listing)

    assert repository.find_by_company(company_id) == (
        historical_listing,
        current_listing,
    )
    assert repository.find_by_company(CompanyId("company-missing")) == ()

"""Integration tests for SEC company-identity ingestion."""

from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from stock_dd.collectors.sec import SECCompanyIdentityCollector
from stock_dd.models import (
    CompanyId,
    CompanyListingId,
)
from stock_dd.repositories.sqlite import (
    SQLiteCompanyListingRepository,
    SQLiteCompanyRepository,
)
from stock_dd.services import CompanyIdentityIngestionService
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema

TEST_USER_AGENT = "Stock DD MAS test@example.com"

FIXED_COLLECTION_TIME = datetime(2026, 8, 28, 14, 30, tzinfo=UTC)

SEC_PAYLOAD: dict[str, object] = {
    "fields": [
        "cik",
        "name",
        "ticker",
        "exchange",
    ],
    "data": [
        [
            320193,
            "Apple Inc.",
            "AAPL",
            "Nasdaq",
        ],
    ],
}


def test_sec_identity_ingestion_persists_and_reuses_sqlite_records(
    sqlite_database_path: Path,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=SEC_PAYLOAD,
        )

    collector = SECCompanyIdentityCollector(
        TEST_USER_AGENT,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_COLLECTION_TIME,
    )

    dataset = collector.collect(" aapl ")

    company_id = CompanyId("company-apple")
    listing_id = CompanyListingId("listing-apple-nasdaq")

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        company_repository = SQLiteCompanyRepository(connection)
        listing_repository = SQLiteCompanyListingRepository(connection)

        service = CompanyIdentityIngestionService(
            company_repository,
            listing_repository,
            company_id_factory=lambda: company_id,
            listing_id_factory=lambda: listing_id,
        )

        with transaction(connection):
            first_result = service.ingest(dataset)

        assert first_result.company_created is True
        assert first_result.listing_created is True
        assert first_result.company.company_id == company_id
        assert first_result.listing is not None
        assert first_result.listing.listing_id == listing_id

    with open_sqlite_database(sqlite_database_path) as connection:
        company_repository = SQLiteCompanyRepository(connection)
        listing_repository = SQLiteCompanyListingRepository(connection)

        persisted_company = company_repository.find_by_cik("0000320193")

        assert persisted_company is not None
        assert persisted_company.company_id == company_id
        assert persisted_company.legal_name == "Apple Inc."

        listings = listing_repository.find_by_company(company_id)

        assert len(listings) == 1

        persisted_listing = listings[0]

        assert persisted_listing.listing_id == listing_id
        assert persisted_listing.ticker == "AAPL"
        assert persisted_listing.exchange == "Nasdaq"

        # SEC collection time must not be treated as listing history
        assert persisted_listing.valid_from is None
        assert persisted_listing.valid_to is None

        assert listing_repository.find_by_ticker(
            "aapl",
            as_of_date=date(2026, 8, 28),
            exchange="nasdaq",
        ) == (persisted_listing,)

        service = CompanyIdentityIngestionService(
            company_repository,
            listing_repository,
        )

        with transaction(connection):
            second_result = service.ingest(dataset)

        assert second_result.company_created is False
        assert second_result.listing_created is False
        assert second_result.company.company_id == company_id
        assert second_result.listing == persisted_listing

        assert company_repository.find_by_cik("0000320193") == persisted_company
        assert listing_repository.find_by_company(company_id) == (persisted_listing,)

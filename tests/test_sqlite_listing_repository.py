"""Test for SQLite company-listing repository implementation."""

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from stock_dd.models import (
    CompanyId,
    CompanyListing,
    CompanyListingId,
)
from stock_dd.repositories import CompanyListingRepository
from stock_dd.repositories.sqlite import (
    SQLiteCompanyListingRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def _insert_company(
    connection: sqlite3.Connection,
    *,
    company_id: str = "company-example",
    cik: str = "0000000001",
) -> None:
    connection.execute(
        """
        INSERT INTO companies (
            company_id,
            legal_name,
            cik
        )
        VALUES(?, ?, ?)
        """,
        (
            company_id,
            "Example Corporation",
            cik,
        ),
    )


def _make_listing(
    *,
    listing_id: str = "listing-example",
    company_id: CompanyId | None = None,
    ticker: str = "EXMP",
    exchange: str = "NASDAQ",
    valid_from: date | None = None,
    valid_to: date | None = None,
    is_active: bool = True,
) -> CompanyListing:
    return CompanyListing(
        listing_id=CompanyListingId(listing_id),
        company_id=CompanyId("company-example") if company_id is None else company_id,
        ticker=ticker,
        exchange=exchange,
        security_name="Common Stock",
        valid_from=valid_from,
        valid_to=valid_to,
        is_active=is_active,
    )


def test_sqlite_listing_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCompanyListingRepository(connection)

        assert isinstance(repository, CompanyListingRepository)


def test_sqlite_listing_repository_round_trips_listing(
    sqlite_database_path: Path,
) -> None:
    listing = _make_listing(
        valid_from=date(2020, 1, 15),
        valid_to=date(2025, 6, 30),
        is_active=False,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(listing)

        assert repository.get(listing.listing_id) == listing


def test_sqlite_listing_repository_returns_none_for_missing_listing(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        reppository = SQLiteCompanyListingRepository(connection)

        assert reppository.get(CompanyListingId("listing-missing")) is None


def test_sqlite_listing_repository_resolves_historical_ticker(
    sqlite_database_path: Path,
) -> None:
    historical = _make_listing(
        listing_id="listing-old",
        ticker="OLD",
        valid_from=date(2018, 1, 1),
        valid_to=date(2022, 12, 31),
        is_active=False,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(historical)

        assert repository.find_by_ticker("OLD", as_of_date=date(2020, 6, 1)) == (
            historical,
        )

        assert repository.find_by_ticker(
            "OLD",
            as_of_date=date(2022, 12, 31),
        ) == (historical,)

        assert (
            repository.find_by_ticker(
                "OLD",
                as_of_date=date(2023, 1, 1),
            )
            == ()
        )


def test_sqlite_listing_repository_handles_open_validity_dates(
    sqlite_database_path: Path,
) -> None:
    listing = _make_listing(
        valid_from=None,
        valid_to=None,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(listing)

        assert repository.find_by_ticker(
            "EXMP",
            as_of_date=date(2000, 1, 1),
        ) == (listing,)

        assert repository.find_by_ticker(
            "EXMP",
            as_of_date=date(2030, 1, 1),
        ) == (listing,)


def test_sqlite_liting_repository_matches_ticker_case_insensitively(
    sqlite_database_path: Path,
) -> None:
    listing = _make_listing(
        ticker="EXMP",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(listing)

        assert repository.find_by_ticker(
            "exmp",
            as_of_date=date(2026, 1, 1),
        ) == (listing,)


def test_sqlite_listing_repository_can_filter_by_exchange(
    sqlite_database_path: Path,
) -> None:
    nasdaq = _make_listing(
        listing_id="listing-nasdaq",
        exchange="NASDAQ",
    )

    tsx = _make_listing(
        listing_id="listing-tsx",
        company_id=CompanyId("company-other"),
        exchange="TSX",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

            _insert_company(
                connection,
                company_id="company-other",
                cik="0000000002",
            )

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(nasdaq)
            repository.save(tsx)

        assert repository.find_by_ticker(
            "EXMP",
            as_of_date=date(2026, 1, 1),
        ) == (
            nasdaq,
            tsx,
        )

        assert repository.find_by_ticker(
            "EXMP",
            as_of_date=date(2026, 1, 1),
            exchange="nasdaq",
        ) == (nasdaq,)


def test_sqlite_listing_repository_finds_company_listing_history(
    sqlite_database_path: Path,
) -> None:
    old = _make_listing(
        listing_id="listing-old",
        ticker="OLD",
        valid_from=date(2018, 1, 1),
        valid_to=date(2022, 12, 31),
        is_active=False,
    )

    current = _make_listing(
        listing_id="listing-current",
        ticker="NEW",
        valid_from=date(2023, 1, 1),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(old)
            repository.save(current)

        assert repository.find_by_company(CompanyId("company-example")) == (
            old,
            current,
        )


def test_sqlite_listing_repository_replaces_same_listing_id(
    sqlite_database_path: Path,
) -> None:
    original = _make_listing(
        valid_from=None,
    )

    updated = CompanyListing(
        listing_id=original.listing_id,
        company_id=original.company_id,
        ticker=original.ticker,
        exchange=original.exchange,
        security_name="Class A Common Stock",
        valid_from=date(2020, 1, 1),
        valid_to=None,
        is_active=True,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.listing_id) == updated


def test_sqlite_listing_repository_does_not_commit_its_own_transaction(
    sqlite_database_path: Path,
) -> None:
    listing = _make_listing()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)

        repository = SQLiteCompanyListingRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(listing)

                raise RuntimeError("force rollback")

        assert repository.get(listing.listing_id) is None

"""Tests for SQLite company repository implementations."""

from pathlib import Path

import pytest

from stock_dd.models import CompanyId, CompanyIdentity
from stock_dd.repositories import CompanyRepository
from stock_dd.repositories.sqlite import SQLiteCompanyRepository
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def test_sqlite_company_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCompanyRepository(connection)

        assert isinstance(repository, CompanyRepository)


def test_sqlite_company_repository_round_trips_company(
    sqlite_database_path: Path,
) -> None:
    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
        is_active=True,
        alternate_names=(
            "Apple Computer Inc.",
            "Apple Computer",
        ),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        with transaction(connection):
            repository.save(company)

        assert repository.get(company.company_id) == company


def test_sqlite_company_repository_finds_company_by_cik(
    sqlite_database_path: Path,
) -> None:
    company = CompanyIdentity(
        company_id=CompanyId("company-apple"),
        legal_name="Apple Inc.",
        cik="0000320193",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        with transaction(connection):
            repository.save(company)

        assert repository.find_by_cik("0000320193") == company


def test_sqlite_company_repository_returns_none_for_midding_company(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        assert repository.get(CompanyId("company-missing")) is None

        assert repository.find_by_cik("0000000000") is None


def test_sqlite_company_repository_replaces_existing_company(
    sqlite_database_path: Path,
) -> None:
    original = CompanyIdentity(
        company_id=CompanyId("company-example"),
        legal_name="Example Corporation",
        cik="0000000001",
        alternate_names=(
            "Example Corp.",
            "Old Example",
        ),
    )

    updated = CompanyIdentity(
        company_id=original.company_id,
        legal_name="Example Holdings Corporation",
        cik="0000000001",
        is_active=False,
        alternate_names=("Example Corporation",),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.company_id) == updated


def test_sqlite_company_repository_does_not_commit_its_own_transaction(
    sqlite_database_path: Path,
) -> None:
    company = CompanyIdentity(
        company_id=CompanyId("company-example"),
        legal_name="Example Corporation",
        cik="0000000001",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(company)

                raise RuntimeError("force rollback")

        assert repository.get(company.company_id) is None


def test_sqlite_company_repository_persists_after_reopening_database(
    sqlite_database_path: Path,
) -> None:
    company = CompanyIdentity(
        company_id=CompanyId("company-example"),
        legal_name="Example Corporation",
        cik="0000000001",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)
        repository = SQLiteCompanyRepository(connection)

        with transaction(connection):
            repository.save(company)

    with open_sqlite_database(sqlite_database_path) as connection:
        repository = SQLiteCompanyRepository(connection)

        assert repository.get(company.company_id) == company

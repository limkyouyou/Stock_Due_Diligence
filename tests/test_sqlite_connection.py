"""Tests for SQLite connection and transaction utilities."""

import sqlite3
from pathlib import Path

import pytest

from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def test_open_sqlite_database_creates_parent_directory(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nested" / "database" / "stock_dd.sqlite3"

    assert not database_path.parent.exists()

    with open_sqlite_database(database_path):
        pass

    assert database_path.exists()


def test_open_sqlite_database_closes_connection(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_open_sqlite_database_uses_row_factory(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        connection.execute(
            """
            CREATE TABLE example (
                example_id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO example(
                example_id,
                name
            )
            VALUES (?, ?)
            """,
            (
                "example-one",
                "Example",
            ),
        )

        row = connection.execute(
            """
            SELECT example_id, name
            FROM example
            """
        ).fetchone()

        assert row is not None
        assert row["example_id"] == "example-one"
        assert row["name"] == "Example"


def test_open_sqlite_database_enforces_foreign_keys(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO company_listings (
                    listing_id,
                    company_id,
                    ticker,
                    exchange
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "listing-example",
                    "company-missing",
                    "EXMP",
                    "NASDAQ",
                ),
            )


def test_transaction_commits_on_success(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            connection.execute(
                """
                INSERT INTO companies (
                    company_id,
                    legal_name,
                    cik
                )
                VALUES (?, ?, ?)
                """,
                (
                    "company-example",
                    "Example Corporation",
                    "0000000001",
                ),
            )

    with open_sqlite_database(sqlite_database_path) as connection:
        row = connection.execute(
            """
            SELECT legal_name
            FROM companies
            WHERE company_id = ?
            """,
            ("company-example",),
        ).fetchone()

    assert row is not None
    assert row["legal_name"] == "Example Corporation"


def test_transaction_rolls_back_on_error(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                connection.execute(
                    """
                    INSERT INTO companies (
                        company_id,
                        legal_name,
                        cik
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        "company-example",
                        "Example Corporation",
                        "0000000001",
                    ),
                )

                raise RuntimeError("test failure")

        row = connection.execute(
            """
            SELECT company_id
            FROM companies
            WHERE company_id = ?
            """,
            ("company-example",),
        ).fetchone()

    assert row is None


def test_transaction_rejects_nested_transaction(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        with transaction(connection):
            with pytest.raises(RuntimeError):
                with transaction(connection):
                    pass

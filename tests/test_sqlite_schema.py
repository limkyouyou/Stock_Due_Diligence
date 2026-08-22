"""Test for SQLite schema initialization."""

import sqlite3
from pathlib import Path

import pytest

from stock_dd.storage.sqlite_schema import (
    SCHEMA_VERSION,
    initialize_schema,
)


def test_initializa_schema_creates_expected_tables(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = {row[0] for row in rows}

    assert {
        "schema_metadata",
        "companies",
        "company_alternate_names",
        "company_listings",
        "evidence_sources",
        "executives",
        "executive_alternate_names",
        "executive_citations",
        "executive_roles",
        "executive_role_citations",
        "career_positions",
        "career_position_citations",
        "company_events",
        "company_event_citations",
        "company_event_executives",
        "company_event_roles",
        "candidate_evidence",
    } <= table_names


def test_initialize_schema_records_schema_version(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)

        row = connection.execute(
            """
            SELECT schema_version
            FROM schema_metadata
            WHERE singleton = 1
            """
        ).fetchone()

    assert row == (SCHEMA_VERSION,)


def test_initialize_schema_can_run_multiple_times(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)
        initialize_schema(connection)

        row = connection.execute(
            """
            SELECT schema_version
            FROM schema_metadata
            WHERE singleton = 1
            """
        ).fetchone()

        assert row == (SCHEMA_VERSION,)


def test_companies_require_unique_cik(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)

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
                "company-one",
                "Example One Inc.",
                "0000000001",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
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
                    "company-two",
                    "Example Two Inc.",
                    "0000000001",
                ),
            )


def test_company_listing_rejects_invalidity_range(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)

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

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO company_listings (
                    listing_id,
                    company_id,
                    ticker,
                    exchange,
                    valid_from,
                    valid_to
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "listing-example",
                    "company-example",
                    "EXMP",
                    "NASDAQ",
                    "2025-01-01",
                    "2024-01-01",
                ),
            )


def test_executive_role_rejects_day_without_month(
    sqlite_database_path: Path,
) -> None:
    with sqlite3.connect(sqlite_database_path) as connection:
        initialize_schema(connection)

        connection.execute(
            """
            INSERT INTO companies (
                company_id,
                legal_name,
                cik
            )
            VALUES ('company-example', 'Example Corp.', '0000000001')
            """
        )

        connection.execute(
            """
            INSERT INTO executives (
                executive_id,
                full_name
            )
            VALUES ('executive-example', 'Jane Smith')
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO executive_roles (
                    role_id,
                    company_id,
                    executive_id,
                    role_type,
                    reported_title,
                    started_year,
                    started_day
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "role-example",
                    "company-example",
                    "executive-example",
                    "chief_executive_officer",
                    "Chief Executive Officer",
                    2022,
                    15,
                ),
            )

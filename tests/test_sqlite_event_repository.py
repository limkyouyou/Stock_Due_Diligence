"""Tests for SQLite company-event repository implementation."""

import sqlite3
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from stock_dd.models import (
    CompanyEvent,
    CompanyEventId,
    CompanyEventType,
    CompanyId,
    EvidenceCitation,
    EvidenceSourceId,
    ExecutiveId,
    ExecutiveRoleId,
    PartialDate,
)
from stock_dd.repositories import CompanyEventRepository
from stock_dd.repositories.sqlite import (
    SQLiteCompanyEventRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def _insert_company(
    connection: sqlite3.Connection,
) -> None:
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


def _insert_executive(
    connection: sqlite3.Connection,
    *,
    executive_id: str = "executive-jane-smith",
    full_name: str = "Jane Smith",
) -> None:
    connection.execute(
        """
        INSERT INTO executives (
            executive_id,
            full_name
        )
        VALUES (?, ?)
        """,
        (
            executive_id,
            full_name,
        ),
    )


def _insert_evidence_source(
    connection: sqlite3.Connection,
    *,
    source_id: str = "source-company-event",
) -> None:
    connection.execute(
        """
        INSERT INTO evidence_sources (
            source_id,
            source_type,
            title,
            publisher,
            retrieved_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            source_id,
            "company_document",
            "Leadership Announcement",
            "Example Corporation",
            "2026-08-26T12:00:00-04:00",
        ),
    )


def _insert_role(
    connection: sqlite3.Connection,
    *,
    role_id: str = "role-example-ceo",
    executive_id: str = "executive-jane-smith",
    role_type: str = "chief_executive_officer",
    reported_title: str = "Chief Executive Officer",
) -> None:
    connection.execute(
        """
        INSERT INTO executive_roles (
            role_id,
            company_id,
            executive_id,
            role_type,
            reported_title
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            role_id,
            "company-example",
            executive_id,
            role_type,
            reported_title,
        ),
    )


def _make_company_event(
    *,
    event_id: str = "event-jane-appointed",
    event_type: CompanyEventType = CompanyEventType.EXECUTIVE_APPOINTMENT,
    related_executive_ids: tuple[ExecutiveId, ...] | None = None,
    related_role_ids: tuple[ExecutiveRoleId, ...] = (),
) -> CompanyEvent:
    return CompanyEvent(
        event_id=CompanyEventId(event_id),
        company_id=CompanyId("company-example"),
        event_type=event_type,
        description="Jane Smith was appointed Chief Executive Officer.",
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-company-event"),
                supporting_excerpt="Jane Smith was appointed Chief Executive Officer.",
                location="Leadership announcement",
            ),
        ),
        announced_on=date(2022, 6, 15),
        occurred_on=PartialDate(
            year=2022,
            month=7,
        ),
        related_executive_ids=(ExecutiveId("executive-jane-smith"),)
        if related_executive_ids is None
        else related_executive_ids,
        related_role_ids=related_role_ids,
    )


def test_sqlite_company_event_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCompanyEventRepository(connection)

        assert isinstance(repository, CompanyEventRepository)


def test_sqlite_company_event_repository_round_trips_event(
    sqlite_database_path: Path,
) -> None:
    role_id = ExecutiveRoleId("role-example-ceo")

    event = _make_company_event(
        related_role_ids=(role_id,),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)
            _insert_role(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(event)

        assert repository.get(event.event_id) == event


def test_sqlite_company_event_repository_returns_none_for_missing_event(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCompanyEventRepository(connection)

        assert repository.get(CompanyEventId("event-missing")) is None


def test_sqlite_company_event_repository_filters_company_by_type(
    sqlite_database_path: Path,
) -> None:
    appointment = _make_company_event(event_id="event-a-appointment")

    departure = _make_company_event(
        event_id="event-b-departure",
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(appointment)
            repository.save(departure)

        assert repository.find_by_company(CompanyId("company-example")) == (
            appointment,
            departure,
        )

        assert repository.find_by_company(
            CompanyId("company-example"),
            event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
        ) == (departure,)


def test_sqlite_company_event_repository_replaces_related_records(
    sqlite_database_path: Path,
) -> None:
    original = _make_company_event(
        related_role_ids=(ExecutiveRoleId("role-example-ceo"),),
    )

    updated = replace(
        original,
        description="Jane Smith changed executive roles.",
        event_type=CompanyEventType.EXECUTIVE_ROLE_CHANGE,
        occurred_on=PartialDate(year=2022),
        related_role_ids=(),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)
            _insert_role(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.event_id) == updated


def test_sqlite_company_event_repository_does_not_commit_own_transaction(
    sqlite_database_path: Path,
) -> None:
    event = _make_company_event()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(event)

                raise RuntimeError("force rollback")

        assert repository.get(event.event_id) is None


def test_sqlite_company_event_repository_finds_events_by_executive(
    sqlite_database_path: Path,
) -> None:
    event = _make_company_event()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(event)

        assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
            event,
        )


def test_sqlite_company_event_repository_finds_events_by_role(
    sqlite_database_path: Path,
) -> None:
    role_id = ExecutiveRoleId("role-example-ceo")
    event = _make_company_event(
        related_role_ids=(role_id,),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)
            _insert_role(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(event)

        assert repository.find_by_role(role_id) == (event,)


def test_sqlite_company_event_repository_filters_executive_by_event_type(
    sqlite_database_path: Path,
) -> None:
    executive_id = ExecutiveId("executive-jane-smith")

    appointment = _make_company_event(
        event_id="event-a-appointment",
        event_type=CompanyEventType.EXECUTIVE_APPOINTMENT,
    )

    departure = _make_company_event(
        event_id="event-b-departure",
        event_type=CompanyEventType.EXECUTIVE_DEPARTURE,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(connection)

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(appointment)
            repository.save(departure)

        assert repository.find_by_executive(
            executive_id, event_type=CompanyEventType.EXECUTIVE_DEPARTURE
        ) == (departure,)


def test_sqlite_company_event_repository_preserves_relationship_order(
    sqlite_database_path: Path,
) -> None:
    executive_a = ExecutiveId("executive-a")
    executive_b = ExecutiveId("executive-b")

    role_a = ExecutiveRoleId("role-a")
    role_b = ExecutiveRoleId("role-b")

    event = _make_company_event(
        related_executive_ids=(
            executive_b,
            executive_a,
        ),
        related_role_ids=(
            role_b,
            role_a,
        ),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(
                connection,
                executive_id="executive-a",
                full_name="Alice Example",
            )
            _insert_executive(
                connection,
                executive_id="executive-b",
                full_name="Bob Example",
            )
            _insert_evidence_source(connection)
            _insert_role(
                connection,
                role_id="role-a",
                executive_id="executive-a",
                role_type="chief_executive_officer",
                reported_title="Chief Executive Officer",
            )
            _insert_role(
                connection,
                role_id="role-b",
                executive_id="executive-b",
                role_type="chief_financial_officer",
                reported_title="Chief Financial Officer",
            )

        repository = SQLiteCompanyEventRepository(connection)

        with transaction(connection):
            repository.save(event)

        loaded = repository.get(event.event_id)

        assert loaded is not None

        assert loaded.related_executive_ids == (
            executive_b,
            executive_a,
        )

        assert loaded.related_role_ids == (
            role_b,
            role_a,
        )

"""Tests for SQLite executive repository implementations."""

import sqlite3
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from stock_dd.models import (
    CompanyId,
    EvidenceCitation,
    EvidenceSourceId,
    Executive,
    ExecutiveId,
    ExecutiveRole,
    ExecutiveRoleId,
    ExecutiveRoleType,
    PartialDate,
)
from stock_dd.repositories import (
    ExecutiveRepository,
    ExecutiveRoleRepository,
)
from stock_dd.repositories.sqlite import (
    SQLiteExecutiveRepository,
    SQLiteExecutiveRoleRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def _insert_evidence_source(
    connection: sqlite3.Connection,
    *,
    source_id: str = "source-executive-biography",
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
            "company_webpage",
            "Leadership Biography",
            "Example Corporation",
            "2026-08-23T16:00:00+00:00",
        ),
    )


def _make_executive(
    *,
    executive_id: str = "executive-jane-smith",
) -> Executive:
    return Executive(
        executive_id=ExecutiveId("Jane Alexandra Smith"),
        full_name="Jane Alexandra Smith",
        alternate_names=(
            "Jane Smith",
            "J. A. Smith",
        ),
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-executive-biography"),
                supporting_excerpt="Jane Alexandrea Smith serves as CEO",
                location="Leadership",
            ),
        ),
    )


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


def _insert_executive(
    connection: sqlite3.Connection,
    *,
    executive_id: str = "executive-jane-smith",
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
            "Jane Smith",
        ),
    )


def _make_executive_role(
    *,
    role_id: str = "role-jane-smith-ceo",
    company_id: CompanyId | None = None,
    executive_id: ExecutiveId | None = None,
    role_type: ExecutiveRoleType = ExecutiveRoleType.CHIEF_EXECUTIVE_OFFICER,
    citation_source_id: str = "source-executive-role",
) -> ExecutiveRole:
    return ExecutiveRole(
        role_id=ExecutiveRoleId(role_id),
        company_id=CompanyId("company-example") if company_id is None else company_id,
        executive_id=ExecutiveId("executive-jane-smith")
        if executive_id is None
        else executive_id,
        role_type=role_type,
        reported_title="Chief Executive Officer",
        started_on=PartialDate(
            year=2022,
        ),
        ended_on=PartialDate(
            year=2025,
            month=6,
        ),
        appointment_announced_on=date(
            2022,
            6,
            15,
        ),
        departure_announced_on=date(
            2025,
            5,
            20,
        ),
        is_interim=False,
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId(citation_source_id),
                supporting_excerpt=(
                    "Jane Smith was appointed Chief Executive Officer."
                ),
                location="Leadership announcement",
            ),
        ),
    )


def test_sqlite_executive_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRepository(connection)

        assert isinstance(
            repository,
            ExecutiveRepository,
        )


def test_sqlite_executive_repository_round_trips_executive(
    sqlite_database_path: Path,
) -> None:
    executive = _make_executive()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteExecutiveRepository(connection)

        with transaction(connection):
            repository.save(executive)

        assert repository.get(executive.executive_id) == executive


def test_sqlite_executive_repository_returns_none_for_missing_executive(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRepository(connection)

        assert repository.get(ExecutiveId("executive-missing")) is None


def test_sqlite_executive_repository_replaces_existing_executive(
    sqlite_database_path: Path,
) -> None:
    original = _make_executive()

    updated = replace(
        original,
        full_name="Jane A. Smith",
        alternate_names=("Jane Alexandra, Smith",),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteExecutiveRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.executive_id) == updated


def test_sqlite_executive_repository_replaces_citations(
    sqlite_database_path: Path,
) -> None:
    original = _make_executive()

    updated = replace(
        original,
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-refulatory-filing"),
                supporting_excerpt="Jane A. Smith is Chief Executive Officer.",
                location="Executive Officers",
            ),
        ),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

            _insert_evidence_source(
                connection,
                source_id="source-refulatory-filing",
            )

        repository = SQLiteExecutiveRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.executive_id) == updated


def test_sqlite_executive_repository_does_not_commit_own_transaction(
    sqlite_database_path: Path,
) -> None:
    executive = _make_executive()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteExecutiveRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(executive)

                raise RuntimeError("force rollback")

        assert repository.get(executive.executive_id) is None


def test_sqlite_executive_repository_requires_existing_evidence_source(
    sqlite_database_path: Path,
) -> None:
    executive = _make_executive()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRepository(connection)

        with pytest.raises(sqlite3.IntegrityError):
            with transaction(connection):
                repository.save(executive)

        assert repository.get(executive.executive_id) is None


def test_sqlite_executive_repository_persists_after_reopening(
    sqlite_database_path: Path,
) -> None:
    executive = _make_executive()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteExecutiveRepository(connection)

        with transaction(connection):
            repository.save(executive)

    with open_sqlite_database(sqlite_database_path) as connection:
        repository = SQLiteExecutiveRepository(connection)

        assert repository.get(executive.executive_id) == executive


def test_sqlite_executive_role_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRoleRepository(connection)

        assert isinstance(
            repository,
            ExecutiveRoleRepository,
        )


def test_sqlite_executive_role_repository_round_trips_role(
    sqlite_database_path: Path,
) -> None:
    role = _make_executive_role()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with transaction(connection):
            repository.save(role)

        assert repository.get(role.role_id) == role


def test_sqlite_executive_role_repository_returns_none_for_missing_role(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRoleRepository(connection)

        assert repository.get(ExecutiveRoleId("role-missing")) is None


def test_sqlite_executive_role_repository_finds_roles_by_executive(
    sqlite_database_path: Path,
) -> None:
    ceo = _make_executive_role(
        role_id="role-a-ceo",
    )

    president = _make_executive_role(
        role_id="role-b-president",
        role_type=ExecutiveRoleType.PRESIDENT,
    )

    other = _make_executive_role(
        role_id="role-c-other",
        executive_id=ExecutiveId("executive-other"),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_executive(
                connection,
                executive_id="executive-other",
            )
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with transaction(connection):
            repository.save(ceo)
            repository.save(president)
            repository.save(other)

        assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
            ceo,
            president,
        )


def test_sqlite_executive_role_repository_filters_company_by_role_type(
    sqlite_database_path: Path,
) -> None:
    ceo = _make_executive_role(role_id="role-a-ceo")

    cfo = _make_executive_role(
        role_id="role-b-cfo",
        executive_id=ExecutiveId("executive-cfo"),
        role_type=ExecutiveRoleType.CHIEF_FINANCIAL_OFFICER,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_executive(
                connection,
                executive_id="executive-cfo",
            )
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with transaction(connection):
            repository.save(ceo)
            repository.save(cfo)

        assert repository.find_by_company(CompanyId("company-example")) == (
            ceo,
            cfo,
        )

        assert repository.find_by_company(
            CompanyId("company-example"),
            role_type=ExecutiveRoleType.CHIEF_FINANCIAL_OFFICER,
        ) == (cfo,)


def test_sqlite_executive_role_repository_replaces_existing_role(
    sqlite_database_path: Path,
) -> None:
    original = _make_executive_role()

    updated = replace(
        original,
        reported_title="President and Chief Executive Officer",
        ended_on=None,
        departure_announced_on=None,
        is_interim=True,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.role_id) == updated


def test_sqlite_executive_role_repository_replaces_citations(
    sqlite_database_path: Path,
) -> None:
    original = _make_executive_role()

    updated = replace(
        original,
        citations=(
            EvidenceCitation(
                source_id=EvidenceSourceId("source-role-filing"),
                supporting_excerpt="Jane Smith serves as CEO.",
                location="Executive Officers",
            ),
        ),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )
            _insert_evidence_source(
                connection,
                source_id="source-role-filing",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.role_id) == updated


def test_sqlite_executive_role_repository_does_not_commit_own_transaction(
    sqlite_database_path: Path,
) -> None:
    role = _make_executive_role()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_company(connection)
            _insert_executive(connection)
            _insert_evidence_source(
                connection,
                source_id="source-executive-role",
            )

        repository = SQLiteExecutiveRoleRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(role)

                raise RuntimeError("force rollback")

        assert repository.get(role.role_id) is None


def test_sqlite_executive_role_repository_requires_parent_records(
    sqlite_database_path: Path,
) -> None:
    role = _make_executive_role()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteExecutiveRoleRepository(connection)

        with pytest.raises(sqlite3.IntegrityError):
            with transaction(connection):
                repository.save(role)

        assert repository.get(role.role_id) is None

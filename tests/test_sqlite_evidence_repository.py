"""Tests for SQLite evidence repository implementations."""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from stock_dd.models import (
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
)
from stock_dd.repositories import EvidenceSourceRepository
from stock_dd.repositories.sqlite import (
    SQLiteEvidenceSourceRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def _make_evidence_source(
    *,
    source_id: str = "source-example",
    source_type: EvidenceSourceType = EvidenceSourceType.REGULATORY_FILING,
    external_id: str | None = "0000320193-26-000001",
) -> EvidenceSource:
    return EvidenceSource(
        source_id=EvidenceSourceId(source_id),
        source_type=source_type,
        title="Example Filing",
        publisher="U.S. Securities and Exchange Commission",
        retrieved_at=datetime(2026, 8, 23, 10, 30, tzinfo=UTC),
        published_on=date(2026, 8, 20),
        url="https://example.com/filing",
        external_id=external_id,
        filing_form="8-K",
        raw_file_path="data/raw/sec/example.html",
        sha256="example-sha256",
        language="en",
    )


def test_sqlite_evidence_source_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        assert isinstance(
            repository,
            EvidenceSourceRepository,
        )


def test_sqlite_evidence_source_repository_round_trips_source(
    sqlite_database_path: Path,
) -> None:
    source = _make_evidence_source()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with transaction(connection):
            repository.save(source)

        assert repository.get(source.source_id) == source


def test_sqlite_evidence_source_repository_returns_none_for_missing_source(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        assert repository.get(EvidenceSourceId("source-missing")) is None


def test_sqlite_evidence_source_repository_finds_external_id(
    sqlite_database_path: Path,
) -> None:
    source = _make_evidence_source()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with transaction(connection):
            repository.save(source)

        assert repository.find_by_external_id("0000320193-26-000001") == (source,)


def test_sqlite_evidence_source_repository_filters_external_id_by_type(
    sqlite_database_path: Path,
) -> None:
    filing = _make_evidence_source(
        source_id="source-filing",
        source_type=EvidenceSourceType.REGULATORY_FILING,
        external_id="external-123",
    )

    regular_data = _make_evidence_source(
        source_id="source-regulator-data",
        source_type=EvidenceSourceType.REGULATOR_DATA,
        external_id="external-123",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with transaction(connection):
            repository.save(filing)
            repository.save(regular_data)

        assert repository.find_by_external_id("external-123") == (
            filing,
            regular_data,
        )

        assert repository.find_by_external_id(
            "external-123", source_type=EvidenceSourceType.REGULATORY_FILING
        ) == (filing,)


def test_sqlite_evidence_source_repository_replaces_same_source_id(
    sqlite_database_path: Path,
) -> None:
    original = _make_evidence_source()

    updated = EvidenceSource(
        source_id=original.source_id,
        source_type=original.source_type,
        title="Updated Filing Tile",
        publisher=original.publisher,
        retrieved_at=original.retrieved_at,
        published_on=original.published_on,
        url=original.url,
        external_id=original.external_id,
        filing_form="10-K",
        raw_file_path=original.raw_file_path,
        sha256="updated-sha256",
        language=original.language,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with transaction(connection):
            repository.save(original)

        with transaction(connection):
            repository.save(updated)

        assert repository.get(original.source_id) == updated


def test_sqlite_evidence_source_repository_does_not_commit_its_own_transaction(
    sqlite_database_path: Path,
) -> None:
    source = _make_evidence_source()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(source)

                raise RuntimeError("force rollback")

        assert repository.get(source.source_id) is None


def test_sqlite_evidence_source_repository_persists_after_reopening(
    sqlite_database_path: Path,
) -> None:
    source = _make_evidence_source()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteEvidenceSourceRepository(connection)

        with transaction(connection):
            repository.save(source)

    with open_sqlite_database(sqlite_database_path) as connection:
        repository = SQLiteEvidenceSourceRepository(connection)

        assert repository.get(source.source_id) == source

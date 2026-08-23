"""Tests for SQLite candidate-evidence persistence."""

import sqlite3
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from stock_dd.models import (
    CandidateClaimType,
    CandidateEvidence,
    CandidateEvidenceId,
    CandidateSubjectType,
    CandidateValue,
    CompanyId,
    EvidenceCitation,
    EvidenceSourceId,
    ExecutiveId,
    ExtractionMethod,
    PartialDate,
    VerificationStatus,
)
from stock_dd.repositories import CandidateEvidenceRepository
from stock_dd.repositories.sqlite import (
    SQLiteCandidateEvidenceRepository,
)
from stock_dd.storage.sqlite_connection import (
    open_sqlite_database,
    transaction,
)
from stock_dd.storage.sqlite_schema import initialize_schema


def _insert_evidence_source(
    connection: sqlite3.Connection,
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
            "source-example",
            "company_document",
            "Example Document",
            "Example Corporation",
            "2026-08-23T10:00:00+00:00",
        ),
    )


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
            "executive-jane-smith",
            "Jane Smith",
        ),
    )


def _make_candidate(
    *,
    candidate_id: str = "candidate-example",
    extracted_value: CandidateValue = "Jane Smith",
    verification_status: VerificationStatus = VerificationStatus.UNREVIEWED,
    company_id: CompanyId | None = None,
    executive_id: ExecutiveId | None = None,
    rejection_reason: str | None = None,
) -> CandidateEvidence:
    return CandidateEvidence(
        candidate_id=CandidateEvidenceId(candidate_id),
        subject_type=CandidateSubjectType.EXECUTIVE,
        subject_name="Jane Smith",
        claim_type=CandidateClaimType.EXECUTIVE_FULL_NAME,
        extracted_value=extracted_value,
        citation=EvidenceCitation(
            source_id=EvidenceSourceId("source-example"),
            supporting_excerpt="Jane Smith serves as Chief Executive Officer.",
            location="Leadership biography",
        ),
        extraction_method=ExtractionMethod.RESEARCH_AGENT,
        extracted_at=datetime(2026, 8, 23, 14, 0, tzinfo=UTC),
        verification_status=verification_status,
        extraction_confidence=0.92,
        company_id=company_id,
        executive_id=executive_id,
        rejection_reason=rejection_reason,
    )


def test_sqlite_candidate_repository_satisfies_contract(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        assert isinstance(
            repository,
            CandidateEvidenceRepository,
        )


@pytest.mark.parametrize(
    "extracted_value",
    [
        "Jane Smith",
        42,
        42.5,
        True,
        date(2024, 6, 15),
        PartialDate(year=2024, month=6),
    ],
)
def test_sqlite_candidate_repository_round_trips_value_types(
    sqlite_database_path: Path,
    extracted_value: CandidateValue,
) -> None:
    candidate = _make_candidate(extracted_value=extracted_value)

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(candidate)

        assert repository.get(candidate.candidate_id) == candidate


def test_sqlite_candidate_repository_returns_none_for_missing_candidate(
    sqlite_database_path: Path,
) -> None:
    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        assert repository.get(CandidateEvidenceId("candidate-missing")) is None


def test_sqlite_candidate_repository_finds_company_candidates(
    sqlite_database_path: Path,
) -> None:
    unreviewed = _make_candidate(
        candidate_id="candidate-unreviewed",
        company_id=CompanyId("company-example"),
    )

    confirmed = _make_candidate(
        candidate_id="candidate-confirmed",
        company_id=CompanyId("company-example"),
        verification_status=VerificationStatus.PRIMARY_SOURCE_CONFIRMED,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)
            _insert_company(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(unreviewed)
            repository.save(confirmed)

        assert repository.find_by_company(CompanyId("company-example")) == (
            confirmed,
            unreviewed,
        )

        assert repository.find_by_company(
            CompanyId("company-example"),
            verification_status=VerificationStatus.UNREVIEWED,
        ) == (unreviewed,)


def test_sqlite_candidate_repository_finds_executive_candidate(
    sqlite_database_path: Path,
) -> None:
    candidate = _make_candidate(
        executive_id=ExecutiveId("executive-jane-smith"),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)
            _insert_executive(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(candidate)

        assert repository.find_by_executive(ExecutiveId("executive-jane-smith")) == (
            candidate,
        )


def test_sqlite_candidate_repository_finds_candidate_by_status(
    sqlite_database_path: Path,
) -> None:
    unreviewed = _make_candidate(
        candidate_id="candidate-unreviewed",
    )

    disputed = _make_candidate(
        candidate_id="candidate-disputed",
        verification_status=VerificationStatus.DISPUTED,
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(unreviewed)
            repository.save(disputed)

        assert repository.find_by_status(VerificationStatus.DISPUTED) == (disputed,)


def test_sqlite_candidate_repository_replaces_candidate_after_review(
    sqlite_database_path: Path,
) -> None:
    candidate = _make_candidate()

    confirmed = replace(
        candidate,
        verification_status=(VerificationStatus.PRIMARY_SOURCE_CONFIRMED),
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(candidate)

        with transaction(connection):
            repository.save(confirmed)

        assert repository.get(candidate.candidate_id) == confirmed

        assert repository.find_by_status(VerificationStatus.UNREVIEWED) == ()

        assert repository.find_by_status(
            VerificationStatus.PRIMARY_SOURCE_CONFIRMED
        ) == (confirmed,)


def test_sqlite_candidate_repository_round_trips_rejected_candidate(
    sqlite_database_path: Path,
) -> None:
    candidate = _make_candidate(
        verification_status=VerificationStatus.REJECTED,
        rejection_reason="Source does not support the claim.",
    )

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with transaction(connection):
            repository.save(candidate)

        assert repository.get(candidate.candidate_id) == candidate


def test_sqlite_candidate_repository_does_does_not_commit_own_transaction(
    sqlite_database_path: Path,
) -> None:
    candidate = _make_candidate()

    with open_sqlite_database(sqlite_database_path) as connection:
        initialize_schema(connection)

        with transaction(connection):
            _insert_evidence_source(connection)

        repository = SQLiteCandidateEvidenceRepository(connection)

        with pytest.raises(RuntimeError):
            with transaction(connection):
                repository.save(candidate)

                raise RuntimeError("force rollback")

        assert repository.get(candidate.candidate_id) is None

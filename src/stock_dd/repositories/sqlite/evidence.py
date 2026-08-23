"""SQLite repository implementations for research evidence."""

import json
import sqlite3
from datetime import date, datetime
from typing import cast

from stock_dd.models import (
    CandidateClaimType,
    CandidateEvidence,
    CandidateEvidenceId,
    CandidateSubjectType,
    CandidateValue,
    CompanyId,
    EvidenceCitation,
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
    ExecutiveId,
    ExtractionMethod,
    PartialDate,
    VerificationStatus,
)


def _serialize_candidate_value(
    value: CandidateValue,
) -> tuple[str, str]:
    """Serialize a candidate value with an explicit storage type."""

    if isinstance(value, str):
        return "str", json.dumps(value)

    if isinstance(value, bool):
        return "bool", json.dumps(value)

    if isinstance(value, int):
        return "int", json.dumps(value)

    if isinstance(value, float):
        return "float", json.dumps(value)

    if isinstance(value, PartialDate):
        return (
            "partial_date",
            json.dumps(
                {
                    "year": value.year,
                    "month": value.month,
                    "day": value.day,
                },
                sort_keys=True,
            ),
        )

    if isinstance(value, date):
        return "date", json.dumps(value.isoformat())

    raise TypeError(f"Unsupported candidate value type: {type(value).__name__}")


def _deserialize_candidate_value(
    value_type: str,
    value_json: str,
) -> CandidateValue:
    """Deserialize a stored candidate value."""

    decoded: object = json.loads(value_json)

    if value_type == "str":
        if not isinstance(decoded, str):
            raise ValueError("Stored candidate string is invalud")

        return decoded

    if value_type == "bool":
        if not isinstance(decoded, bool):
            raise ValueError("Stored candidate boolean is invalid")

        return decoded

    if value_type == "int":
        if not isinstance(decoded, int):
            raise ValueError("Stored candidate integer is invalid")

        return decoded

    if value_type == "float":
        if not isinstance(decoded, float):
            raise ValueError("Stored candidate float is invalid")

        return decoded

    if value_type == "date":
        if not isinstance(decoded, str):
            raise ValueError("Stored candidate date is invalid")

        return date.fromisoformat(decoded)

    if value_type == "partial_date":
        if not isinstance(decoded, dict):
            raise ValueError("Stored candidate partial date is invalid")

        payload = cast(dict[str, object], decoded)

        year = payload.get("year")
        month = payload.get("month")
        day = payload.get("day")

        if not isinstance(year, int) or isinstance(year, bool):
            raise ValueError("Stored candidate partial-date year is invalid")

        if month is not None and (
            not isinstance(month, int) or isinstance(month, bool)
        ):
            raise ValueError("Stored candidate partial-date month is invalid")

        if day is not None and (not isinstance(day, int) or isinstance(day, bool)):
            raise ValueError("Stored candidate partial-date day is invalid")

        return PartialDate(year=year, month=month, day=day)

    raise ValueError(f"Unkown candidate value type: {value_type}")


class SQLiteEvidenceSourceRepository:
    """SQLite persistence for external research sources."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, source: EvidenceSource) -> None:
        """Insert or update an evidence source."""

        self._connection.execute(
            """
            INSERT INTO evidence_sources (
                source_id,
                source_type,
                title,
                publisher,
                retrieved_at,
                published_on,
                url,
                external_id,
                filing_form,
                raw_file_path,
                sha256,
                language
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type = excluded.source_type,
                title = excluded.title,
                publisher = excluded.publisher,
                retrieved_at = excluded.retrieved_at,
                published_on = excluded.published_on,
                url = excluded.url,
                external_id = excluded.external_id,
                filing_form = excluded.filing_form,
                raw_file_path = excluded.raw_file_path,
                sha256 = excluded.sha256,
                language = excluded.language
            """,
            (
                source.source_id,
                source.source_type.value,
                source.title,
                source.publisher,
                source.retrieved_at.isoformat(),
                source.published_on.isoformat()
                if source.published_on is not None
                else None,
                source.url,
                source.external_id,
                source.filing_form,
                source.raw_file_path,
                source.sha256,
                source.language,
            ),
        )

    def get(
        self,
        source_id: EvidenceSourceId,
    ) -> EvidenceSource | None:
        """Return an evidence source by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                source_id,
                source_type,
                title,
                publisher,
                retrieved_at,
                published_on,
                url,
                external_id,
                filing_form,
                raw_file_path,
                sha256,
                language
            FROM evidence_sources
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchone()

        if row is None:
            return None

        return self._source_from_row(row)

    def find_by_external_id(
        self,
        external_id: str,
        *,
        source_type: EvidenceSourceType | None = None,
    ) -> tuple[EvidenceSource, ...]:
        """Return evidence sources matching an external identifier."""

        source_type_value = source_type.value if source_type is not None else None

        rows = self._connection.execute(
            """
            SELECT
                source_id,
                source_type,
                title,
                publisher,
                retrieved_at,
                published_on,
                url,
                external_id,
                filing_form,
                raw_file_path,
                sha256,
                language
            FROM evidence_sources
            WHERE external_id = ?
                AND (
                    ? IS NULL
                    OR source_type = ?
                )
            ORDER BY source_id
            """,
            (
                external_id,
                source_type_value,
                source_type_value,
            ),
        ).fetchall()

        return tuple(self._source_from_row(row) for row in rows)

    @staticmethod
    def _source_from_row(row: sqlite3.Row) -> EvidenceSource:
        """Convert an evidence-source database row into a domain object."""

        return EvidenceSource(
            source_id=EvidenceSourceId(row["source_id"]),
            source_type=EvidenceSourceType(row["source_type"]),
            title=row["title"],
            publisher=row["publisher"],
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
            published_on=date.fromisoformat(row["published_on"])
            if row["published_on"] is not None
            else None,
            url=row["url"],
            external_id=row["external_id"],
            filing_form=row["filing_form"],
            raw_file_path=row["raw_file_path"],
            sha256=row["sha256"],
            language=row["language"],
        )


class SQLiteCandidateEvidenceRepository:
    """SQLite persistence for candidate research claims."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, candidate: CandidateEvidence) -> None:
        """Insert or update a candidate evidence record."""

        value_type, value_json = _serialize_candidate_value(candidate.extracted_value)

        self._connection.execute(
            """
            INSERT INTO candidate_evidence (
                candidate_id,
                subject_type,
                subject_name,
                claim_type,
                extracted_value_type,
                extracted_value_json,
                source_id,
                citation_supporting_excerpt,
                citation_location,
                extraction_method,
                extracted_at,
                verification_status,
                extraction_confidence,
                rejection_reason,
                company_id,
                executive_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
                subject_type = excluded.subject_type,
                subject_name = excluded.subject_name,
                claim_type = excluded.claim_type,
                extracted_value_type = excluded.extracted_value_type,
                extracted_value_json = excluded.extracted_value_json,
                source_id = excluded.source_id,
                citation_supporting_excerpt = excluded.citation_supporting_excerpt,
                citation_location = excluded.citation_location,
                extraction_method = excluded.extraction_method,
                extracted_at = excluded.extracted_at,
                verification_status = excluded.verification_status,
                extraction_confidence = excluded.extraction_confidence,
                rejection_reason = excluded.rejection_reason,
                company_id = excluded.company_id,
                executive_id = excluded.executive_id                
            """,
            (
                candidate.candidate_id,
                candidate.subject_type.value,
                candidate.subject_name,
                candidate.claim_type.value,
                value_type,
                value_json,
                candidate.citation.source_id,
                candidate.citation.supporting_excerpt,
                candidate.citation.location,
                candidate.extraction_method.value,
                candidate.extracted_at.isoformat(),
                candidate.verification_status.value,
                candidate.extraction_confidence,
                candidate.rejection_reason,
                candidate.company_id,
                candidate.executive_id,
            ),
        )

    def get(
        self,
        candidate_id: CandidateEvidenceId,
    ) -> CandidateEvidence | None:
        """Return candidate evidence by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                candidate_id,
                subject_type,
                subject_name,
                claim_type,
                extracted_value_type,
                extracted_value_json,
                source_id,
                citation_supporting_excerpt,
                citation_location,
                extraction_method,
                extracted_at,
                verification_status,
                extraction_confidence,
                rejection_reason,
                company_id,
                executive_id
            FROM candidate_evidence
            WHERE candidate_id = ?                
            """,
            (candidate_id,),
        ).fetchone()

        if row is None:
            return None

        return self._candidate_from_row(row)

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence associated with a company."""

        status_value = (
            verification_status.value if verification_status is not None else None
        )

        rows = self._connection.execute(
            """
            SELECT
                candidate_id,
                subject_type,
                subject_name,
                claim_type,
                extracted_value_type,
                extracted_value_json,
                source_id,
                citation_supporting_excerpt,
                citation_location,
                extraction_method,
                extracted_at,
                verification_status,
                extraction_confidence,
                rejection_reason,
                company_id,
                executive_id
            FROM candidate_evidence
            WHERE company_id = ?
                AND (
                    ? IS NULL
                    OR verification_status = ?
                )
            ORDER BY candidate_id
            """,
            (
                company_id,
                status_value,
                status_value,
            ),
        ).fetchall()

        return tuple(self._candidate_from_row(row) for row in rows)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        verification_status: VerificationStatus | None = None,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence associated with an executive."""

        status_value = (
            verification_status.value if verification_status is not None else None
        )

        rows = self._connection.execute(
            """
            SELECT
                candidate_id,
                subject_type,
                subject_name,
                claim_type,
                extracted_value_type,
                extracted_value_json,
                source_id,
                citation_supporting_excerpt,
                citation_location,
                extraction_method,
                extracted_at,
                verification_status,
                extraction_confidence,
                rejection_reason,
                company_id,
                executive_id
            FROM candidate_evidence
            WHERE executive_id = ?
                AND (
                    ? IS NULL
                    OR verification_status = ?
                )
            ORDER BY candidate_id
            """,
            (
                executive_id,
                status_value,
                status_value,
            ),
        ).fetchall()

        return tuple(self._candidate_from_row(row) for row in rows)

    def find_by_status(
        self,
        verification_status: VerificationStatus,
    ) -> tuple[CandidateEvidence, ...]:
        """Return candidate evidence with a verification status."""

        rows = self._connection.execute(
            """
            SELECT
                candidate_id,
                subject_type,
                subject_name,
                claim_type,
                extracted_value_type,
                extracted_value_json,
                source_id,
                citation_supporting_excerpt,
                citation_location,
                extraction_method,
                extracted_at,
                verification_status,
                extraction_confidence,
                rejection_reason,
                company_id,
                executive_id
            FROM candidate_evidence
            WHERE verification_status = ?
            ORDER BY candidate_id
            """,
            (verification_status.value,),
        ).fetchall()

        return tuple(self._candidate_from_row(row) for row in rows)

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> CandidateEvidence:
        """Convert a candidate database row into a domain object."""

        return CandidateEvidence(
            candidate_id=CandidateEvidenceId(row["candidate_id"]),
            subject_type=CandidateSubjectType(row["subject_type"]),
            subject_name=row["subject_name"],
            claim_type=CandidateClaimType(row["claim_type"]),
            extracted_value=_deserialize_candidate_value(
                row["extracted_value_type"],
                row["extracted_value_json"],
            ),
            citation=EvidenceCitation(
                source_id=EvidenceSourceId(row["source_id"]),
                supporting_excerpt=row["citation_supporting_excerpt"],
                location=row["citation_location"],
            ),
            extraction_method=ExtractionMethod(row["extraction_method"]),
            extracted_at=datetime.fromisoformat(row["extracted_at"]),
            verification_status=VerificationStatus(row["verification_status"]),
            extraction_confidence=row["extraction_confidence"],
            rejection_reason=row["rejection_reason"],
            company_id=row["company_id"],
            executive_id=(
                ExecutiveId(row["executive_id"])
                if row["executive_id"] is not None
                else None
            ),
        )

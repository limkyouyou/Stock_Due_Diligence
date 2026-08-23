"""SQLite repository implementations for research evidence."""

import sqlite3
from datetime import date, datetime

from stock_dd.models import (
    EvidenceSource,
    EvidenceSourceId,
    EvidenceSourceType,
)


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

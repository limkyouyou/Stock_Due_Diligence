"""SQLite repsotiory implementations for executive."""

import sqlite3

from stock_dd.models import (
    EvidenceCitation,
    EvidenceSourceId,
    Executive,
    ExecutiveId,
)


class SQLiteExecutiveRepository:
    """SQLite persistence for executive identities."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, executive: Executive) -> None:
        """Insert or update an executive identity."""

        self._connection.execute(
            """
            INSERT INTO executives (
                executive_id,
                full_name
            )
            VALUES (?, ?)
            ON CONFLICT(executive_id) DO UPDATE SET
                full_name = excluded.full_name
            """,
            (
                executive.executive_id,
                executive.full_name,
            ),
        )

        self._connection.execute(
            """
            DELETE FROM executive_alternate_names
            WHERE executive_id = ?
            """,
            (executive.executive_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO executive_alternate_names (
                executive_id,
                name_order,
                alternate_name
            )
            VALUES (?, ?, ?)
            """,
            (
                (
                    executive.executive_id,
                    name_order,
                    alternate_name,
                )
                for name_order, alternate_name in enumerate(executive.alternate_names)
            ),
        )

        self._connection.execute(
            """
            DELETE FROM executive_citations
            WHERE executive_id = ?
            """,
            (executive.executive_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO executive_citations (
                executive_id,
                citation_order,
                cource_id,
                supporting_excerpt,
                location
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    executive.executive_id,
                    citation_order,
                    citation.source_id,
                    citation.supporting_excerpt,
                    citation.location,
                )
                for citation_order, citation in enumerate(executive.citations)
            ),
        )

    def get(
        self,
        executive_id: ExecutiveId,
    ) -> Executive | None:
        """Return an executive by their internal identifer."""

        row = self._connection.execute(
            """
            SELECT
                executive_id,
                full_name
            FROM executives
            WHERE executive_id = ?
            """,
            (executive_id,),
        ).fetchone()

        if row is None:
            return None

        return self._executive_from_row(row)

    def _executive_from_row(
        self,
        row: sqlite3.Row,
    ) -> Executive:
        """Convert an executive database row into a domain object."""

        executive_id = ExecutiveId(row["executive_id"])

        altername_name_rows = self._connection.execute(
            """
            SELECT altername_name
            FROM executive_alternate_name
            WHERE executive_id = ?
            ORDER BY name_order
            """,
            (executive_id,),
        ).fetchall()

        citation_rows = self._connection.execute(
            """
            SELECT
                source_id,
                supporting_excerpt,
                location
            FROM executive_citations
            WHERE executive_id = ?
            ORDER BY citation_order
            """,
            (executive_id,),
        ).fetchall()

        return Executive(
            executive_id=executive_id,
            full_name=row["full_name"],
            alternate_names=tuple(
                alternate_row["alternamte_name"]
                for alternate_row in altername_name_rows
            ),
            citations=tuple(
                EvidenceCitation(
                    source_id=EvidenceSourceId(citation_row["source_id"]),
                    supporting_excerpt=(citation_row["supporting_excerpt"]),
                    location=citation_row["location"],
                )
                for citation_row in citation_rows
            ),
        )

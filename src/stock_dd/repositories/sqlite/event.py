"""SQLite repository implementation for company events."""

import sqlite3
from datetime import date

from stock_dd.models import (
    CompanyEvent,
    CompanyEventId,
    CompanyEventType,
    CompanyId,
    EvidenceCitation,
    EvidenceSourceId,
    ExecutiveId,
    ExecutiveRoleId,
)
from stock_dd.repositories.sqlite._dates import (
    partial_date_from_row,
    partial_date_to_columns,
)


class SQLiteCompanyEventRepository:
    """SQLite persistence for researched company events."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, event: CompanyEvent) -> None:
        """Insert or update a company event."""

        (
            occurred_year,
            occurred_month,
            occurred_day,
        ) = partial_date_to_columns(event.occurred_on)

        self._connection.execute(
            """
            INSERT INTO company_events (
                event_id,
                company_id,
                event_type,
                description,
                announced_on,
                occurred_year,
                occurred_month,
                occurred_day            
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                company_id = excluded.company_id,
                event_type = excluded.event_type,
                description = excluded.description,
                announced_on = excluded.announced_on,
                occurred_year = excluded.occurred_year,
                occurred_month = excluded.occurred_month,
                occurred_day = excluded.occurred_day                
            """,
            (
                event.event_id,
                event.company_id,
                event.event_type.value,
                event.description,
                event.announced_on.isoformat()
                if event.announced_on is not None
                else None,
                occurred_year,
                occurred_month,
                occurred_day,
            ),
        )

        self._replace_citations(event)
        self._replace_executives(event)
        self._replace_roles(event)

    def _replace_citations(
        self,
        event: CompanyEvent,
    ) -> None:
        """Replace all citations for a company event."""

        self._connection.execute(
            """
            DELETE FROM company_event_citations
            WHERE event_id = ?
            """,
            (event.event_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO company_event_citations (
                event_id,
                citation_order,
                source_id,
                supporting_excerpt,
                location
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    event.event_id,
                    citation_order,
                    citation.source_id,
                    citation.supporting_excerpt,
                    citation.location,
                )
                for citation_order, citation in enumerate(event.citations)
            ),
        )

    def _replace_executives(
        self,
        event: CompanyEvent,
    ) -> None:
        """Replace executives associated with a company event."""

        self._connection.execute(
            """
            DELETE FROM company_event_executives
            WHERE event_id = ?
            """,
            (event.event_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO company_event_executives (
                event_id,
                executive_order,
                executive_id
            )
            VALUES (?, ?, ?)
            """,
            (
                (
                    event.event_id,
                    executive_order,
                    executive_id,
                )
                for executive_order, executive_id in enumerate(
                    event.related_executive_ids
                )
            ),
        )

    def _replace_roles(
        self,
        event: CompanyEvent,
    ) -> None:
        """Replace executive roles associated with a company event."""

        self._connection.execute(
            """
            DELETE FROM company_event_roles
            WHERE event_id = ?
            """,
            (event.event_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO company_event_roles(
                event_id,
                role_order,
                role_id
            )
            VALUES (?, ?, ?)
            """,
            (
                (
                    event.event_id,
                    role_order,
                    role_id,
                )
                for role_order, role_id in enumerate(event.related_role_ids)
            ),
        )

    def get(
        self,
        event_id: CompanyEventId,
    ) -> CompanyEvent | None:
        """Return a company event by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                event_id,
                company_id,
                event_type,
                description,
                announced_on,
                occurred_year,
                occurred_month,
                occurred_day
            FROM company_events
            WHERE event_id = ?                
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        return self._event_from_row(row)

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with a company."""

        event_type_value = event_type.value if event_type is not None else None

        rows = self._connection.execute(
            """
            SELECT
                event_id,
                company_id,
                event_type,
                description,
                announced_on,
                occurred_year,
                occurred_month,
                occurred_day
            FROM company_events
            WHERE company_id = ?
                AND (
                    ? IS NULL
                    OR event_type = ?
                )            
            ORDER BY event_id
            """,
            (
                company_id,
                event_type_value,
                event_type_value,
            ),
        ).fetchall()

        return tuple(self._event_from_row(row) for row in rows)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
        *,
        event_type: CompanyEventType | None = None,
    ) -> tuple[CompanyEvent, ...]:
        """Return events associated with an executive."""

        event_type_value = event_type.value if event_type is not None else None

        rows = self._connection.execute(
            """
            SELECT
                event.event_id,
                event.company_id,
                event.event_type,
                event.description,
                event.announced_on,
                event.occurred_year,
                event.occurred_month,
                event.occurred_day
            FROM company_events AS event
            JOIN company_event_executives AS related
                ON related.event_id = event.event_id
            WHERE related.executive_id = ?
                AND (
                    ? IS NULL
                    OR event.event_type = ?
                )            
            ORDER BY event.event_id
            """,
            (
                executive_id,
                event_type_value,
                event_type_value,
            ),
        ).fetchall()

        return tuple(self._event_from_row(row) for row in rows)

    def find_by_role(self, role_id: ExecutiveRoleId) -> tuple[CompanyEvent, ...]:
        """Return events associated with an executive role."""

        rows = self._connection.execute(
            """
            SELECT
                event.event_id,
                event.company_id,
                event.event_type,
                event.description,
                event.announced_on,
                event.occurred_year,
                event.occurred_month,
                event.occurred_day
            FROM company_events AS event
            JOIN company_event_roles AS related
                ON related.event_id = event.event_id
            WHERE related.role_id = ?
            ORDER BY event.event_id
            """,
            (role_id,),
        ).fetchall()

        return tuple(self._event_from_row(row) for row in rows)

    def _event_from_row(
        self,
        row: sqlite3.Row,
    ) -> CompanyEvent:
        """Convert a company-event row into a domain object."""

        event_id = CompanyEventId(row["event_id"])

        citation_rows = self._connection.execute(
            """
            SELECT
                source_id,
                supporting_excerpt,
                location
            FROM company_event_citations
            WHERE event_id = ?
            ORDER BY citation_order
            """,
            (event_id,),
        ).fetchall()

        executive_rows = self._connection.execute(
            """
            SELECT executive_id
            FROM company_event_executives
            WHERE event_id = ?
            ORDER BY executive_order
            """,
            (event_id,),
        ).fetchall()

        role_rows = self._connection.execute(
            """
            SELECT role_id
            FROM company_event_roles
            WHERE event_id = ?
            ORDER BY role_order
            """,
            (event_id,),
        ).fetchall()

        return CompanyEvent(
            event_id=event_id,
            company_id=CompanyId(row["company_id"]),
            event_type=CompanyEventType(row["event_type"]),
            description=row["description"],
            citations=tuple(
                EvidenceCitation(
                    source_id=EvidenceSourceId(citation_row["source_id"]),
                    supporting_excerpt=citation_row["supporting_excerpt"],
                    location=citation_row["location"],
                )
                for citation_row in citation_rows
            ),
            announced_on=date.fromisoformat(row["announced_on"])
            if row["announced_on"] is not None
            else None,
            occurred_on=partial_date_from_row(
                row,
                "occurred",
            ),
            related_executive_ids=tuple(
                ExecutiveId(executive_row["executive_id"])
                for executive_row in executive_rows
            ),
            related_role_ids=tuple(
                ExecutiveRoleId(role_row["role_id"]) for role_row in role_rows
            ),
        )

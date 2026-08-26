"""SQLite repsotiory implementations for executive."""

import sqlite3
from datetime import date

from stock_dd.models import (
    CareerPosition,
    CareerPositionId,
    CompanyId,
    EvidenceCitation,
    EvidenceSourceId,
    Executive,
    ExecutiveId,
    ExecutiveRole,
    ExecutiveRoleId,
    ExecutiveRoleType,
)
from stock_dd.repositories.sqlite._dates import (
    partial_date_from_row,
    partial_date_to_columns,
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
                source_id,
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

        alternate_name_rows = self._connection.execute(
            """
            SELECT alternate_name
            FROM executive_alternate_names
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
                alternate_row["alternate_name"] for alternate_row in alternate_name_rows
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


class SQLiteExecutiveRoleRepository:
    """SQLite persistence for executive company roles."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, role: ExecutiveRole) -> None:
        """Insert or update an executive role."""

        (
            started_year,
            started_month,
            started_day,
        ) = partial_date_to_columns(role.started_on)

        (
            ended_year,
            ended_month,
            ended_day,
        ) = partial_date_to_columns(role.ended_on)

        self._connection.execute(
            """
            INSERT INTO executive_roles (
                role_id,
                company_id,
                executive_id,
                role_type,
                reported_title,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
                appointment_announced_on,
                departure_announced_on,
                is_interim                
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(role_id) DO UPDATE SET
                company_id = excluded.company_id,
                executive_id = excluded.executive_id,
                role_type = excluded.role_type,
                reported_title = excluded.reported_title,
                started_year = excluded.started_year,
                started_month = excluded.started_month,
                started_day = excluded.started_day,
                ended_year = excluded.ended_year,
                ended_month = excluded.ended_month,
                ended_day = excluded.ended_day,
                appointment_announced_on = excluded.appointment_announced_on,
                departure_announced_on = excluded.departure_announced_on,
                is_interim = excluded.is_interim                
            """,
            (
                role.role_id,
                role.company_id,
                role.executive_id,
                role.role_type.value,
                role.reported_title,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
                role.appointment_announced_on.isoformat()
                if role.appointment_announced_on is not None
                else None,
                role.departure_announced_on.isoformat()
                if role.departure_announced_on is not None
                else None,
                int(role.is_interim),
            ),
        )

        self._connection.execute(
            """
            DELETE FROM executive_role_citations
            WHERE role_id = ?
            """,
            (role.role_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO executive_role_citations (
                role_id,
                citation_order,
                source_id,
                supporting_excerpt,
                location
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    role.role_id,
                    citation_order,
                    citation.source_id,
                    citation.supporting_excerpt,
                    citation.location,
                )
                for citation_order, citation in enumerate(role.citations)
            ),
        )

    def get(
        self,
        role_id: ExecutiveRoleId,
    ) -> ExecutiveRole | None:
        """Return an executive role by its internal identifer."""

        row = self._connection.execute(
            """
            SELECT
                role_id,
                company_id,
                executive_id,
                role_type,
                reported_title,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
                appointment_announced_on,
                departure_announced_on,
                is_interim
            FROM executive_roles
            WHERE role_id = ?                
            """,
            (role_id,),
        ).fetchone()

        if row is None:
            return None

        return self._role_from_row(row)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[ExecutiveRole, ...]:
        """Return all known roles for an executive."""

        rows = self._connection.execute(
            """
            SELECT
                role_id,
                company_id,
                executive_id,
                role_type,
                reported_title,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
                appointment_announced_on,
                departure_announced_on,
                is_interim
            FROM executive_roles
            WHERE executive_id = ?
            ORDER BY role_id                
            """,
            (executive_id,),
        ).fetchall()

        return tuple(self._role_from_row(row) for row in rows)

    def find_by_company(
        self,
        company_id: CompanyId,
        *,
        role_type: ExecutiveRoleType | None = None,
    ) -> tuple[ExecutiveRole, ...]:
        """Return executive roles associated with a company."""

        role_type_value = role_type.value if role_type is not None else None

        rows = self._connection.execute(
            """
            SELECT
                role_id,
                company_id,
                executive_id,
                role_type,
                reported_title,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
                appointment_announced_on,
                departure_announced_on,
                is_interim
            FROM executive_roles
            WHERE company_id = ?
                AND (
                    ? IS NULL
                    OR role_type = ?
                )
            ORDER BY role_id                
            """,
            (
                company_id,
                role_type_value,
                role_type_value,
            ),
        ).fetchall()

        return tuple(self._role_from_row(row) for row in rows)

    def _role_from_row(
        self,
        row: sqlite3.Row,
    ) -> ExecutiveRole:
        """Convert an executive-role row into a domain object."""

        role_id = ExecutiveRoleId(row["role_id"])

        citation_rows = self._connection.execute(
            """
            SELECT
                source_id,
                supporting_excerpt,
                location
            FROM executive_role_citations
            WHERE role_id = ?
            ORDER BY citation_order
            """,
            (role_id,),
        ).fetchall()

        return ExecutiveRole(
            role_id=role_id,
            company_id=CompanyId(row["company_id"]),
            executive_id=ExecutiveId(row["executive_id"]),
            role_type=ExecutiveRoleType(row["role_type"]),
            reported_title=row["reported_title"],
            citations=tuple(
                EvidenceCitation(
                    source_id=EvidenceSourceId(citation_row["source_id"]),
                    supporting_excerpt=citation_row["supporting_excerpt"],
                    location=citation_row["location"],
                )
                for citation_row in citation_rows
            ),
            started_on=partial_date_from_row(row, "started"),
            ended_on=partial_date_from_row(row, "ended"),
            appointment_announced_on=(
                date.fromisoformat(row["appointment_announced_on"])
                if row["appointment_announced_on"] is not None
                else None
            ),
            departure_announced_on=(
                date.fromisoformat(row["departure_announced_on"])
                if row["departure_announced_on"] is not None
                else None
            ),
            is_interim=bool(row["is_interim"]),
        )


class SQLiteCareerPositionRepository:
    """SQLite persistence for executive career positions."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, position: CareerPosition) -> None:
        """Insert or update an executive career position."""

        (
            started_year,
            started_month,
            started_day,
        ) = partial_date_to_columns(position.started_on)

        (
            ended_year,
            ended_month,
            ended_day,
        ) = partial_date_to_columns(position.ended_on)

        self._connection.execute(
            """
            INSERT INTO career_positions (
                position_id,
                executive_id,
                employer_name,
                reported_title,
                employer_company_id,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day                
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(position_id) DO UPDATE SET
                executive_id = excluded.executive_id,
                employer_name = excluded.employer_name,
                reported_title = excluded.reported_title,
                employer_company_id = excluded.employer_company_id,
                started_year = excluded.started_year,
                started_month = excluded.started_month,
                started_day = excluded.started_day,
                ended_year = excluded.ended_year,
                ended_month = excluded.ended_month,
                ended_day = excluded.ended_day                
            """,
            (
                position.position_id,
                position.executive_id,
                position.employer_name,
                position.reported_title,
                position.employer_company_id,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day,
            ),
        )

        self._connection.execute(
            """
            DELETE FROM career_position_citations
            WHERE position_id = ?
            """,
            (position.position_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO career_position_citations (
                position_id,
                citation_order,
                source_id,
                supporting_excerpt,
                location
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    position.position_id,
                    citation_order,
                    citation.source_id,
                    citation.supporting_excerpt,
                    citation.location,
                )
                for citation_order, citation in enumerate(position.citations)
            ),
        )

    def get(self, position_id: CareerPositionId) -> CareerPosition | None:
        """Return a career position by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                position_id,
                executive_id,
                employer_name,
                reported_title,
                employer_company_id,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day
            FROM career_positions
            WHERE position_id = ?                
            """,
            (position_id,),
        ).fetchone()

        if row is None:
            return None

        return self._position_from_row(row)

    def find_by_executive(
        self,
        executive_id: ExecutiveId,
    ) -> tuple[CareerPosition, ...]:
        """Return all known career positions for an executive."""

        rows = self._connection.execute(
            """
            SELECT
                position_id,
                executive_id,
                employer_name,
                reported_title,
                employer_company_id,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day
            FROM career_positions
            WHERE executive_id = ?
            ORDER BY position_id
            """,
            (executive_id,),
        ).fetchall()

        return tuple(self._position_from_row(row) for row in rows)

    def find_by_employer_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CareerPosition, ...]:
        """Reutrn positions linked to a known employer company."""

        rows = self._connection.execute(
            """
            SELECT
                position_id,
                executive_id,
                employer_name,
                reported_title,
                employer_company_id,
                started_year,
                started_month,
                started_day,
                ended_year,
                ended_month,
                ended_day
            FROM career_positions
            WHERE employer_company_id = ?
            ORDER by position_id
            """,
            (company_id,),
        ).fetchall()

        return tuple(self._position_from_row(row) for row in rows)

    def _position_from_row(
        self,
        row: sqlite3.Row,
    ) -> CareerPosition:
        """Convert a career-position row into a domain object."""

        position_id = CareerPositionId(row["position_id"])

        citations_rows = self._connection.execute(
            """
            SELECT
                source_id,
                supporting_excerpt,
                location
            FROM career_position_citations
            WHERE position_id = ?
            ORDER BY citation_order
            """,
            (position_id,),
        ).fetchall()

        return CareerPosition(
            position_id=position_id,
            executive_id=ExecutiveId(row["executive_id"]),
            employer_name=row["employer_name"],
            reported_title=row["reported_title"],
            employer_company_id=(
                CompanyId(row["employer_company_id"])
                if row["employer_company_id"] is not None
                else None
            ),
            started_on=partial_date_from_row(
                row,
                "started",
            ),
            ended_on=partial_date_from_row(
                row,
                "ended",
            ),
            citations=tuple(
                EvidenceCitation(
                    source_id=EvidenceSourceId(citation_row["source_id"]),
                    supporting_excerpt=citation_row["supporting_excerpt"],
                    location=citation_row["location"],
                )
                for citation_row in citations_rows
            ),
        )

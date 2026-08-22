"""SQLite repository implementation for company identities."""

import sqlite3

from stock_dd.models import CompanyId, CompanyIdentity


class SQLiteCompanyRepository:
    """SQLite persistence for legal company identities."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, company: CompanyIdentity) -> None:
        """Insert or update a company identity."""

        self._connection.execute(
            """
            INSERT INTO companies (
                company_id,
                legal_name,
                cik,
                is_active
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(company_id) DO UPDATE SET
                legal_name = excluded.legal_name,
                cik = excluded.cik,
                is_active = excluded.is_active
            """,
            (
                company.company_id,
                company.legal_name,
                company.cik,
                company.is_active,
            ),
        )

        self._connection.execute(
            """
            DELETE FROM company_alternate_names
            WHERE company_id = ?
            """,
            (company.company_id,),
        )

        self._connection.executemany(
            """
            INSERT INTO company_alternate_names (
                company_id,
                name_order,
                    alternate_name
            )
            VALUES (?, ?, ?)
            """,
            (
                (
                    company.company_id,
                    name_order,
                    alternate_name,
                )
                for name_order, alternate_name in enumerate(company.alternate_names)
            ),
        )

    def get(
        self,
        company_id: CompanyId,
    ) -> CompanyIdentity | None:
        """Reutrn a company by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                company_id,
                legal_name,
                cik,
                is_active
            FROM companies
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        if row is None:
            return None

        return self._company_from_row(row)

    def find_by_cik(
        self,
        cik: str,
    ) -> CompanyIdentity | None:
        """Return a company by its SEC Central Index Key."""

        row = self._connection.execute(
            """
            SELECT
                company_id,
                legal_name,
                cik,
                is_active
            FROM companies
            WHERE cik = ?
            """,
            (cik,),
        ).fetchone()

        if row is None:
            return None

        return self._company_from_row(row)

    def _company_from_row(
        self,
        row: sqlite3.Row,
    ) -> CompanyIdentity:
        """Convert a company database row into a domain object."""

        company_id = CompanyId(row["company_id"])

        alternate_name_rows = self._connection.execute(
            """
            SELECT alternate_name
            FROM company_alternate_names
            WHERE company_id = ?
            ORDER BY name_order
            """,
            (company_id,),
        ).fetchall()

        return CompanyIdentity(
            company_id=company_id,
            legal_name=row["legal_name"],
            cik=row["cik"],
            is_active=bool(row["is_active"]),
            alternate_names=tuple(
                alternate_row["alternate_name"] for alternate_row in alternate_name_rows
            ),
        )

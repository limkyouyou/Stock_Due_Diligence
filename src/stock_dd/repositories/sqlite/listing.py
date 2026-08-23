"""SQLite repository implementation for company listings."""

import sqlite3
from datetime import date

from stock_dd.models import (
    CompanyId,
    CompanyListing,
    CompanyListingId,
)


class SQLiteCompanyListingRepository:
    """SQLite persistence for publicly traded company listings."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, listing: CompanyListing) -> None:
        """Insert or update a company listing."""

        self._connection.execute(
            """
            INSERT INTO company_listings (
                listing_id,
                company_id,
                ticker,
                exchange,
                security_name,
                valid_from,
                valid_to,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
                company_id = excluded.company_id,
                ticker = excluded.ticker,
                exchange = excluded.exchange,
                security_name = excluded.security_name,
                valid_from = excluded.valid_from,
                valid_to = excluded.valid_to,
                is_active = excluded.is_active
            """,
            (
                listing.listing_id,
                listing.company_id,
                listing.ticker,
                listing.exchange,
                listing.security_name,
                listing.valid_from.isoformat()
                if listing.valid_from is not None
                else None,
                listing.valid_to.isoformat() if listing.valid_to is not None else None,
                int(listing.is_active),
            ),
        )

    def get(
        self,
        listing_id: CompanyListingId,
    ) -> CompanyListing | None:
        """Return a listing by its internal identifier."""

        row = self._connection.execute(
            """
            SELECT
                listing_id,
                company_id,
                ticker,
                exchange,
                security_name,
                valid_from,
                valid_to,
                is_active
            FROM company_listings
            WHERE listing_id = ?
            """,
            (listing_id,),
        ).fetchone()

        if row is None:
            return None

        return self._listing_from_row(row)

    def find_by_ticker(
        self,
        ticker: str,
        *,
        as_of_date: date,
        exchange: str | None = None,
    ) -> tuple[CompanyListing, ...]:
        """Return listings valid for a ticker on a particular date."""

        rows = self._connection.execute(
            """
            SELECT
                listing_id,
                company_id,
                ticker,
                exchange,
                security_name,
                valid_from,
                valid_to,
                is_active
            FROM company_listings
            WHERE ticker = ? COLLATE NOCASE
                AND (
                    ? IS NULL
                    OR exchange = ? COLLATE NOCASE
                )
                AND (
                    valid_from IS NULL
                    OR valid_from <= ?
                )
                AND (
                    valid_to IS NULL
                    OR ? <= valid_to
                )
            ORDER BY
                exchange COLLATE NOCASE,
                valid_from,
                listing_id
            """,
            (
                ticker,
                exchange,
                exchange,
                as_of_date.isoformat(),
                as_of_date.isoformat(),
            ),
        ).fetchall()

        return tuple(self._listing_from_row(row) for row in rows)

    def find_by_company(
        self,
        company_id: CompanyId,
    ) -> tuple[CompanyListing, ...]:
        """Return all known listings associated with a company."""

        rows = self._connection.execute(
            """
            SELECT
                listing_id,
                company_id,
                ticker,
                exchange,
                security_name,
                valid_from,
                valid_to,
                is_active
            FROM company_listings
            WHERE company_id = ?
            ORDER BY
                valid_from,
                listing_id
            """,
            (company_id,),
        ).fetchall()

        return tuple(self._listing_from_row(row) for row in rows)

    @staticmethod
    def _listing_from_row(
        row: sqlite3.Row,
    ) -> CompanyListing:
        """Convert a listing database row into a domain object."""

        return CompanyListing(
            listing_id=CompanyListingId(row["listing_id"]),
            company_id=CompanyId(row["company_id"]),
            ticker=row["ticker"],
            exchange=row["exchange"],
            security_name=row["security_name"],
            valid_from=date.fromisoformat(row["valid_from"])
            if row["valid_from"] is not None
            else None,
            valid_to=date.fromisoformat(row["valid_to"])
            if row["valid_to"] is not None
            else None,
            is_active=bool(row["is_active"]),
        )

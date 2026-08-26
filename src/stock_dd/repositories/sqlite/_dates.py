"""SQLite conversion helpers for partial dates."""

import sqlite3
from typing import cast

from stock_dd.models import PartialDate


def partial_date_to_columns(
    value: PartialDate | None,
) -> tuple[int | None, int | None, int | None]:
    """Convert a partial date into SQLite column values."""

    if value is None:
        return None, None, None

    return value.year, value.month, value.day


def partial_date_from_row(
    row: sqlite3.Row,
    prefix: str,
) -> PartialDate | None:
    """Reconstruct a partial date from SQLite columns."""

    year = cast(
        int | None,
        row[f"{prefix}_year"],
    )
    month = cast(
        int | None,
        row[f"{prefix}_month"],
    )
    day = cast(
        int | None,
        row[f"{prefix}_day"],
    )

    if year is None:
        return None

    return PartialDate(
        year=year,
        month=month,
        day=day,
    )

"""SQLite connection and transaction utilities."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def open_sqlite_database(
    database_path: Path,
) -> Iterator[sqlite3.Connection]:
    """Open a configured SQLite connection and close it on exit."""

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)

    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(
    connection: sqlite3.Connection,
) -> Iterator[None]:
    """Commit a transaction on success and roll it back on failure."""

    if connection.in_transaction:
        raise RuntimeError(
            "Cannot start a transaction while snother transaction is already active."
        )

    connection.execute("BEGIN")

    try:
        yield
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()

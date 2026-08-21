"""Shared pytest fictures for Stock DD MAS tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sqlite_database_path(
    tmp_path: Path,
) -> Path:
    """Return an isolated SQLite database path for one test."""

    return tmp_path / "stock_dd_test.sqlite3"

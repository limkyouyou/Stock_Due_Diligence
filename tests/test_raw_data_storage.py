"""Tests for raw financial-data storage."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from stock_dd.collectors.base import RawFinancialDataset
from stock_dd.exceptions import RawDataStorageError
from stock_dd.storage.raw_data import (
    save_raw_financial_dataset,
)

COLLECTION_TIME = datetime(
    2026,
    7,
    31,
    21,
    30,
    45,
    123456,
    tzinfo=UTC,
)


def create_dataset(
    *,
    provider: str = "fmp",
    ticker: str = "AAPL",
    collected_at: datetime = COLLECTION_TIME,
    payloads: dict[str, object] | None = None,
) -> RawFinancialDataset:
    """Create a raw financial dataset for storage tests."""

    return RawFinancialDataset(
        provider=provider,
        ticker=ticker,
        collected_at=collected_at,
        payloads=payloads
        if payloads is not None
        else {
            "profile": [
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                }
            ],
            "income_statements": [
                {
                    "calendarYear": "2025",
                    "revenue": 100,
                }
            ],
        },
    )


def test_save_raw_financial_dataset_creates_json_envelope(
    tmp_path: Path,
) -> None:
    dataset = create_dataset()

    saved_path = save_raw_financial_dataset(
        dataset,
        tmp_path,
    )

    expected_path = tmp_path / "fmp" / "AAPL" / "20260731T213045123456Z.json"

    assert saved_path == expected_path
    assert saved_path.exists()

    stored_data = json.loads(saved_path.read_text(encoding="utf-8"))

    assert stored_data["schema_version"] == 1
    assert stored_data["provider"] == "fmp"
    assert stored_data["ticker"] == "AAPL"
    assert stored_data["collected_at"] == "2026-07-31T21:30:45.123456Z"
    assert stored_data["payloads"] == dict(dataset.payloads)


def test_save_raw_dataset_normalizes_directory_names(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(
        provider="FMP",
        ticker="aapl",
    )

    saved_path = save_raw_financial_dataset(
        dataset,
        tmp_path,
    )

    assert saved_path.parent == (tmp_path / "fmp" / "AAPL")


def test_save_raw_dataset_converts_timestamp_to_utc(
    tmp_path: Path,
) -> None:
    collection_time = datetime.fromisoformat("2026-07-31T17:30:45.123456-04:00")
    dataset = create_dataset(
        collected_at=collection_time,
    )

    saved_path = save_raw_financial_dataset(
        dataset,
        tmp_path,
    )

    assert saved_path.name == ("20260731T213045123456Z.json")

    stored_data = json.loads(saved_path.read_text(encoding="utf-8"))

    assert stored_data["collected_at"] == "2026-07-31T21:30:45.123456Z"


def test_save_raw_dataset_rejects_naive_datetime(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(
        collected_at=datetime(2026, 7, 31, 21, 30),
    )

    with pytest.raises(
        RawDataStorageError,
        match="timezone-aware",
    ):
        save_raw_financial_dataset(dataset, tmp_path)


@pytest.mark.parametrize(
    ("field_name", "provider", "ticker"),
    [
        ("provider", "../fmp", "AAPL"),
        ("ticker", "fmp", "../../AAPL"),
        ("ticker", "fmp", ""),
    ],
)
def test_save_raw_dataset_rejects_unsafe_path_values(
    tmp_path: Path,
    field_name: str,
    provider: str,
    ticker: str,
) -> None:
    dataset = create_dataset(
        provider=provider,
        ticker=ticker,
    )

    with pytest.raises(
        RawDataStorageError,
        match=field_name,
    ):
        save_raw_financial_dataset(dataset, tmp_path)


def test_save_raw_dataset_does_not_overwrite_existing_file(
    tmp_path: Path,
) -> None:
    dataset = create_dataset()

    first_path = save_raw_financial_dataset(
        dataset,
        tmp_path,
    )

    original_contents = first_path.read_text(encoding="utf-8")

    with pytest.raises(
        RawDataStorageError,
        match="already exists",
    ):
        save_raw_financial_dataset(dataset, tmp_path)

    assert first_path.read_text(encoding="utf-8") == original_contents


def test_save_raw_dataset_rejects_non_json_payload(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(
        payloads={"profile": object()},
    )

    with pytest.raises(
        RawDataStorageError,
        match="Could not save",
    ):
        save_raw_financial_dataset(dataset, tmp_path)

    temporary_files = list(tmp_path.rglob("*.tmp"))

    assert temporary_files == []

"""Test for loading and validating reserach data."""

import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from stock_dd.exceptions import ResearchDataError
from stock_dd.loader import load_research_data


@pytest.fixture
def valid_payload() -> dict[str, Any]:
    """Return valid research data for loader tests."""

    return {
        "metadata": {
            "as_of_date": "2025-12-31",
            "currency": "USD",
            "source": "Test data",
        },
        "company": {
            "ticker": "nstr",
            "name": "Northstar Robotics Inc.",
            "sector": "Industrials",
            "industry": "Industrial Automation",
            "description": "A fictional robotics company.",
        },
        "annual_financials": [
            {
                "fiscal_year": 2025,
                "revenue": 160_000_000,
                "operating_income": 18_000_000,
                "net_income": 12_000_000,
                "cash_and_equivalents": 31_000_000,
                "total_debt": 24_000_000,
                "operating_cash_flow": 24_000_000,
                "capital_expenditures": 7_000_000,
            },
            {
                "fiscal_year": 2024,
                "revenue": 138_000_000,
                "operating_income": 13_000_000,
                "net_income": 8_000_000,
                "cash_and_equivalents": 25_000_000,
                "total_debt": 28_000_000,
                "operating_cash_flow": 18_000_000,
                "capital_expenditures": 6_000_000,
            },
        ],
    }


def write_json_file(
    tmp_path: Path,
    payload: Any,
) -> Path:
    """Write JSON test data to a temporary file."""
    file_path = tmp_path / "research_data.json"
    file_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return file_path


def test_load_research_data_converts_and_sorts_values(
    tmp_path: Path,
    valid_payload: dict[str, Any],
) -> None:
    file_path = write_json_file(tmp_path, valid_payload)

    result = load_research_data(file_path)

    assert result.metadata.as_of_date == date(2025, 12, 31)
    assert result.metadata.currency == "USD"
    assert result.company.ticker == "NSTR"
    assert result.company.name == "Northstar Robotics Inc."

    assert [financial.fiscal_year for financial in result.annual_financials] == [
        2024,
        2025,
    ]

    assert isinstance(result.annual_financials, tuple)


def test_missing_file_raises_research_data_error(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(
        ResearchDataError,
        match="was not found",
    ):
        load_research_data(missing_file)


def test_invalid_json_raises_research_data_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "invalid.json"
    file_path.write_text(
        '{"company": ',
        encoding="utf-8",
    )

    with pytest.raises(
        ResearchDataError,
        match="Invalid JSON",
    ):
        load_research_data(file_path)


def test_missing_required_field_raises_error(
    tmp_path: Path,
    valid_payload: dict[str, Any],
) -> None:
    payload = deepcopy(valid_payload)
    del payload["company"]["ticker"]

    file_path = write_json_file(tmp_path, payload)

    with pytest.raises(
        ResearchDataError,
        match=r"company\.ticker",
    ):
        load_research_data(file_path)


def test_incorrect_field_type_raises_error(
    tmp_path: Path,
    valid_payload: dict[str, Any],
) -> None:
    payload = deepcopy(valid_payload)
    payload["annual_financials"][0]["revenue"] = "160 million"

    file_path = write_json_file(tmp_path, payload)

    with pytest.raises(
        ResearchDataError,
        match=r"annual_financials\[0\]\.revenue",
    ):
        load_research_data(file_path)


def test_duplicate_fiscal_years_raise_error(
    tmp_path: Path,
    valid_payload: dict[str, Any],
) -> None:
    payload = deepcopy(valid_payload)

    duplicate = deepcopy(payload["annual_financials"][0])
    payload["annual_financials"].append(duplicate)

    file_path = write_json_file(tmp_path, payload)

    with pytest.raises(
        ResearchDataError,
        match="duplicate fiscal years",
    ):
        load_research_data(file_path)


def test_empty_financial_records_raise_error(
    tmp_path: Path,
    valid_payload: dict[str, Any],
) -> None:
    payload = deepcopy(valid_payload)
    payload["annual_financials"] = []

    file_path = write_json_file(tmp_path, payload)

    with pytest.raises(
        ResearchDataError,
        match="at least one financial record",
    ):
        load_research_data(file_path)

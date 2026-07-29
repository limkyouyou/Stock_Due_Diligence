"""Load and validate stock due-diligence reserach data from JSON files."""

from __future__ import annotations

import json
from datetime import date
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from stock_dd.exceptions import ResearchDataError
from stock_dd.models import (
    AnnualFinancial,
    Company,
    CompanyResearchData,
    ResearchMetadata,
)


def load_research_data(file_path: str | Path) -> CompanyResearchData:
    """Load company reserach data from a JSON file

    Args:
        file_path: Path to the JSON reserach file.

    Returns:
        Validated company reserach data.

    Raises:
        ResearchDataError: If the file cannot be read or contains invalid data.
    """

    path = Path(file_path)
    raw_data = _read_json(path)

    metadata_data = _require_mapping(
        _required_value(raw_data, "metadata", "root"),
        "metadata",
    )
    company_data = _require_mapping(
        _required_value(raw_data, "company", "root"),
        "company",
    )
    financials_data = _require_list(
        _required_value(raw_data, "annual_financials", "root"),
        "annual_financials",
    )

    metadata = _parse_metadata(metadata_data)
    company = _parse_company(company_data)
    annual_financials = tuple(
        _parse_annual_financial(item, index)
        for index, item in enumerate(financials_data)
    )

    if not annual_financials:
        raise ResearchDataError(
            "'annual_financials' must contain at least one financial record."
        )

    _check_duplicate_fiscal_years(annual_financials)

    sorted_financials = tuple(
        sorted(
            annual_financials,
            key=lambda financial: financial.fiscal_year,
        )
    )

    return CompanyResearchData(
        metadata=metadata,
        company=company,
        annual_financials=sorted_financials,
    )


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file and return its top-level object."""

    try:
        with path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError as error:
        raise ResearchDataError(f"Research data file was not found: {path}") from error
    except PermissionError as error:
        raise ResearchDataError(
            f"Permission was denied when reading: {path}"
        ) from error
    except JSONDecodeError as error:
        raise ResearchDataError(
            f"Invalid JSON in {path} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    except OSError as error:
        raise ResearchDataError(
            f"Could not read research data file {path}: {error}"
        ) from error

    return _require_mapping(raw_data, "root")


def _parse_metadata(data: dict[str, Any]) -> ResearchMetadata:
    """Convert metadata JSON into a ResearchMetadata object."""

    date_text = _require_string(data, "as_of_date", "metadata")

    try:
        as_of_date = date.fromisoformat(date_text)
    except ValueError as error:
        raise ResearchDataError(
            "'metadata.as_of_date' must use YYYY-MM-DD format."
        ) from error

    return ResearchMetadata(
        as_of_date=as_of_date,
        currency=_require_string(data, "currency", "metadata"),
        source=_require_string(data, "source", "metadata"),
    )


def _parse_company(data: dict[str, Any]) -> Company:
    """Convert company JSON into a Company object."""

    return Company(
        ticker=_require_string(data, "ticker", "company").upper(),
        name=_require_string(data, "name", "company"),
        sector=_require_string(data, "sector", "company"),
        industry=_require_string(data, "industry", "company"),
        description=_require_string(data, "description", "company"),
    )


def _parse_annual_financial(
    value: Any,
    index: Any,
) -> AnnualFinancial:
    """Convert one annual financial JSON record into a model."""

    field_path = f"annual_financials[{index}]"
    data = _require_mapping(value, field_path)

    return AnnualFinancial(
        fiscal_year=_require_integer(data, "fiscal_year", field_path),
        revenue=_require_integer(data, "revenue", field_path),
        operating_income=_require_integer(
            data,
            "operating_income",
            field_path,
        ),
        net_income=_require_integer(data, "net_income", field_path),
        cash_and_equivalents=_require_integer(
            data,
            "cash_and_equivalents",
            field_path,
        ),
        total_debt=_require_integer(data, "total_debt", field_path),
        operating_cash_flow=_require_integer(
            data,
            "operating_cash_flow",
            field_path,
        ),
        capital_expenditures=_require_integer(data, "capital_expenditures", field_path),
    )


def _required_value(
    data: dict[str, Any],
    key: str,
    field_path: str,
) -> Any:
    """Return a required value or raise a descriptive error."""

    if key not in data:
        raise ResearchDataError(f"Required field '{field_path}.{key}' is missing.")

    return data[key]


def _require_string(
    data: dict[str, Any],
    key: str,
    field_path: str,
) -> str:
    """Return a required non-empty string."""

    value = _required_value(data, key, field_path)

    if not isinstance(value, str) or not value.strip():
        raise ResearchDataError(f"'{field_path}.{key}' must be a non-empty string.")

    return value.strip()


def _require_integer(
    data: dict[str, Any],
    key: str,
    field_path: str,
) -> int:
    """Return a required integer."""

    value = _required_value(data, key, field_path)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ResearchDataError(f"'{field_path}.{key}' must be an integer.")

    return value


def _require_mapping(value: Any, field_path: str) -> dict[str, Any]:
    """Ensure a value is a JSON object."""

    if not isinstance(value, dict):
        raise ResearchDataError(f"'{field_path}' must be a JSON object.")

    return value


def _require_list(value: Any, field_path: str) -> list[Any]:
    """Ensure a value is a JSON array."""

    if not isinstance(value, list):
        raise ResearchDataError(f"'{field_path}' must be a JSON array")

    return value


def _check_duplicate_fiscal_years(
    financials: tuple[AnnualFinancial, ...],
) -> None:
    """Reject datasets containing duplicate fiscal years."""

    fiscal_years = [financial.fiscal_year for financial in financials]

    if len(fiscal_years) != len(set(fiscal_years)):
        raise ResearchDataError("'annual_financials' contains duplicate fiscal years.")

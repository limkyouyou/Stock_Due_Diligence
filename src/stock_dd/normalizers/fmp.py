"""Normalize FMP responses into Stock DD domain models."""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import cast

from stock_dd.collectors.base import RawFinancialDataset
from stock_dd.exceptions import NormalizationError
from stock_dd.models import (
    AnnualFinancial,
    Company,
    CompanyResearchData,
    ResearchMetadata,
)

type JSONRecord = Mapping[str, object]


_REQUIRED_PAYLOADS = (
    "profile",
    "income_statements",
    "balance_sheets",
    "cash_flow_statements",
)


def normalize_fmp_dataset(
    dataset: RawFinancialDataset,
) -> CompanyResearchData:
    """Convert a raw FMP dataset into provider-independent models."""

    if dataset.provider.strip().lower() != "fmp":
        raise NormalizationError(
            f"The FMP normalizer received data from provider {dataset.provider!r}."
        )

    ticker = dataset.ticker.strip().upper()

    if not ticker:
        raise NormalizationError("The raw financial dataset has an empty ticker.")

    payload_records = {
        payload_name: _require_record_list(
            dataset.payloads,
            payload_name,
        )
        for payload_name in _REQUIRED_PAYLOADS
    }

    profile = _select_profile(
        payload_records["profile"],
        ticker,
    )

    income_by_year = _index_statements(
        payload_records["income_statements"],
        payload_name="income_statements",
        ticker=ticker,
    )
    balance_by_year = _index_statements(
        payload_records["balance_sheets"],
        payload_name="balance_sheets",
        ticker=ticker,
    )
    cash_flow_by_year = _index_statements(
        payload_records["cash_flow_statements"],
        payload_name="cash_flow_statements",
        ticker=ticker,
    )

    fiscal_years = _require_matching_year_coverage(
        income_by_year,
        balance_by_year,
        cash_flow_by_year,
    )

    currency = _require_string(
        profile,
        "currency",
        "profile",
    ).upper()

    _validate_statement_currencies(
        income_by_year,
        balance_by_year,
        cash_flow_by_year,
        expected_currency=currency,
    )

    financials: list[AnnualFinancial] = []
    reporting_dates: list[date] = []

    for fiscal_year in fiscal_years:
        income = income_by_year[fiscal_year]
        balance = balance_by_year[fiscal_year]
        cash_flow = cash_flow_by_year[fiscal_year]

        reporting_date = _require_matching_reporting_date(
            fiscal_year=fiscal_year,
            income=income,
            balance=balance,
            cash_flow=cash_flow,
        )
        reporting_dates.append(reporting_date)

        financials.append(
            AnnualFinancial(
                fiscal_year=fiscal_year,
                revenue=_require_integer(
                    income,
                    "revenue",
                    f"income_statements[{fiscal_year}]",
                ),
                operating_income=_require_integer(
                    income,
                    "operatingIncome",
                    f"income_statements[{fiscal_year}]",
                ),
                net_income=_require_integer(
                    income,
                    "netIncome",
                    f"income_statements[{fiscal_year}]",
                ),
                cash_and_equivalents=_require_integer(
                    balance,
                    "cashAndCashEquivalents",
                    f"balance_sheets[{fiscal_year}]",
                ),
                total_debt=_require_integer(
                    balance,
                    "totalDebt",
                    f"balance_sheets[{fiscal_year}]",
                ),
                operating_cash_flow=_require_integer(
                    cash_flow,
                    "operatingCashFlow",
                    f"cash_flow_statements[{fiscal_year}]",
                ),
                capital_expenditures=abs(
                    _require_integer(
                        cash_flow,
                        "capitalExpenditure",
                        f"cash_flow_statements[{fiscal_year}]",
                    ),
                ),
            )
        )

    return CompanyResearchData(
        metadata=ResearchMetadata(
            as_of_date=max(reporting_dates),
            currency=currency,
            source="Financial Modeling Prep",
        ),
        company=Company(
            ticker=ticker,
            name=_require_string(
                profile,
                "companyName",
                "profile",
            ),
            sector=_require_string(
                profile,
                "sector",
                "profile",
            ),
            industry=_require_string(
                profile,
                "industry",
                "profile",
            ),
            description=_require_string(
                profile,
                "description",
                "profile",
            ),
        ),
        annual_financials=tuple(financials),
    )


def _require_record_list(
    payloads: Mapping[str, object],
    payload_name: str,
) -> tuple[JSONRecord, ...]:
    """Return one required payload as a non-empty list of objects."""

    if payload_name not in payloads:
        raise NormalizationError(f"Required FMP payload '{payload_name}' is missing.")

    value = payloads[payload_name]

    if not isinstance(value, list):
        raise NormalizationError(f"FMP payload '{payload_name}' must be a JSON array.")

    if not value:
        raise NormalizationError(f"FMP payload '{payload_name}' must not be empty.")

    records: list[JSONRecord] = []

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise NormalizationError(
                f"FMP payload '{payload_name}[{index}]' must be a JSON object."
            )

        if not all(isinstance(key, str) for key in item):
            raise NormalizationError(
                f"FMP payload '{payload_name}[{index}]' contains a non-string key."
            )

        records.append(cast(dict[str, object], item))

    return tuple(records)


def _select_profile(
    profiles: Sequence[JSONRecord],
    ticker: str,
) -> JSONRecord:
    """Select the profile matching the requested ticker."""

    matches = [
        profile
        for index, profile in enumerate(profiles)
        if _require_string(
            profile,
            "symbol",
            f"profile[{index}]",
        ).upper()
        == ticker
    ]

    if not matches:
        raise NormalizationError(
            f"FMP profile data does not contain ticker '{ticker}'."
        )

    if len(matches) > 1:
        raise NormalizationError(
            f"FMP returned multiple profiles for ticker '{ticker}'."
        )

    return matches[0]


def _index_statements(
    records: Sequence[JSONRecord],
    *,
    payload_name: str,
    ticker: str,
) -> dict[int, JSONRecord]:
    """Index statement records by fiscal year."""

    indexed: dict[int, JSONRecord] = {}

    for index, record in enumerate(records):
        field_path = f"{payload_name}[{index}]"

        symbol = _require_string(
            record,
            "symbol",
            field_path,
        )

        if symbol != ticker:
            raise NormalizationError(
                f"'{field_path}.symbol' contains '{symbol}', "
                f"but '{ticker}' was expected."
            )

        fiscal_year = _require_fiscal_year(
            record,
            field_path,
        )

        if fiscal_year in indexed:
            raise NormalizationError(
                f"FMP payload '{payload_name}' contains duplicate "
                f"fiscal year {fiscal_year}."
            )

        indexed[fiscal_year] = record

    return indexed


def _require_fiscal_year(
    record: JSONRecord,
    field_path: str,
) -> int:
    """Read fiscalYear or calendarYear from an FMP record."""

    available_years: list[int] = []

    for field_name in ("fiscalYear", "calendarYear"):
        if field_name not in record:
            continue

        value = record[field_name]

        if isinstance(value, bool):
            raise NormalizationError(
                f"'{field_path}.{field_name}' must be a four-digit year."
            )

        if isinstance(value, int):
            year = value
        elif isinstance(value, str):
            year = int(value.strip())
        else:
            raise NormalizationError(
                f"'{field_path}.{field_name}' must be a four-digit year."
            )

        if not 1000 <= year <= 9999:
            raise NormalizationError(
                f"'{field_path}.{field_name}' must be a four digit year."
            )

        available_years.append(year)

    if not available_years:
        raise NormalizationError(
            f"'{field_path}' is missing fiscalYear or calendarYear."
        )

    if len(set(available_years)) != 1:
        raise NormalizationError(
            f"'{field_path}' contains conflicting fiscal-year values."
        )

    return available_years[0]


def _require_matching_year_coverage(
    income_by_year: Mapping[int, JSONRecord],
    balance_by_year: Mapping[int, JSONRecord],
    cash_flow_by_year: Mapping[int, JSONRecord],
) -> tuple[int, ...]:
    """Require all three statements to cover the same fiscal years."""

    income_years = set(income_by_year)
    balance_years = set(balance_by_year)
    cash_flow_years = set(cash_flow_by_year)

    if not (income_years == balance_years == cash_flow_years):
        raise NormalizationError(
            "FMP statement fiscal-year coverage does not match: "
            f"income={sorted(income_years)}, "
            f"balance={sorted(balance_years)}, "
            f"cash_flow={sorted(cash_flow_years)}."
        )

    return tuple(sorted(income_years))


def _require_matching_reporting_date(
    *,
    fiscal_year: int,
    income: JSONRecord,
    balance: JSONRecord,
    cash_flow: JSONRecord,
) -> date:
    """Require all statements for a fiscal year to share one date."""

    dates = {
        _require_date(
            income,
            "date",
            f"income_statements[{fiscal_year}]",
        ),
        _require_date(
            balance,
            "date",
            f"balance_sheets[{fiscal_year}]",
        ),
        _require_date(
            cash_flow,
            "date",
            f"cash_flow_statement[{fiscal_year}]",
        ),
    }

    if len(dates) != 1:
        raise NormalizationError(
            f"FMP statement reporting dates do not match for fiscal year {fiscal_year}."
        )

    return dates.pop()


def _validate_statement_currencies(
    income_by_year: Mapping[int, JSONRecord],
    balance_by_year: Mapping[int, JSONRecord],
    cash_flow_by_year: Mapping[int, JSONRecord],
    *,
    expected_currency: str,
) -> None:
    """Reject statements currencies that conflict with the profile."""

    statement_groups = (
        ("income_statements", income_by_year),
        ("balance_sheets", balance_by_year),
        ("cash_flow_statements", cash_flow_by_year),
    )

    for payload_name, records_by_year in statement_groups:
        for fiscal_year, record in records_by_year.items():
            if "reportedCurrency" not in record:
                continue

            reported_currency = _require_string(
                record,
                "reportedCurrency",
                f"{payload_name}[{fiscal_year}]",
            ).upper()

            if reported_currency != expected_currency:
                raise NormalizationError(
                    f"'{payload_name}[{fiscal_year}].reportedCurrency' "
                    f"is '{reported_currency}', but"
                    f"'{expected_currency}' was expected."
                )


def _require_string(
    record: JSONRecord,
    field_name: str,
    field_path: str,
) -> str:
    """Return a required non-empty string."""

    value = _required_value(
        record,
        field_name,
        field_path,
    )

    if not isinstance(value, str) or not value.strip():
        raise NormalizationError(
            f"'{field_path}.{field_name}' must be a non-empty string."
        )

    return value.strip()


def _require_integer(
    record: JSONRecord,
    field_name: str,
    field_path: str,
) -> int:
    """Return a required integer-valued financial amount."""

    value = _required_value(
        record,
        field_name,
        field_path,
    )

    if isinstance(value, bool):
        raise NormalizationError(f"'{field_path}.{field_name}' must be an integer.")

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer():
        return int(value)

    raise NormalizationError(f"'{field_path}.{field_name}' must be an integer.")


def _require_date(
    record: JSONRecord,
    field_name: str,
    field_path: str,
) -> date:
    """Return a required ISO 8601 date."""

    value = _require_string(
        record,
        field_name,
        field_path,
    )

    try:
        return date.fromisoformat(value)
    except ValueError as err:
        raise NormalizationError(
            f"'{field_path}.{field_name}' must use YYYY-MM-DD format."
        ) from err


def _required_value(
    record: JSONRecord,
    field_name: str,
    field_path: str,
) -> object:
    """Return a required provider field."""

    if field_name not in record:
        raise NormalizationError(f"'{field_path}.{field_name}' is missing.")

    return record[field_name]

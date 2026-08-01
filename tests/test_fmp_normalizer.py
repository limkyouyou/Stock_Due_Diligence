"""Tests for FMP financial-data normalization."""

from datetime import UTC, datetime
from typing import cast

import pytest

from stock_dd.collectors.base import RawFinancialDataset
from stock_dd.exceptions import NormalizationError
from stock_dd.normalizers.fmp import normalize_fmp_dataset

type PayloadRecord = dict[str, object]


COLLECTION_TIME = datetime(
    2026,
    7,
    31,
    22,
    0,
    tzinfo=UTC,
)


def create_payloads() -> dict[str, object]:
    """Create valid synthetic FMP payloads."""

    return {
        "profile": [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "currency": "USD",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "description": "A technology company.",
            }
        ],
        "income_statements": [
            {
                "symbol": "AAPL",
                "fiscalYear": "2025",
                "date": "2025-09-27",
                "reportedCurrency": "USD",
                "revenue": 1000,
                "operatingIncome": 300,
                "netIncome": 200,
            },
            {
                "symbol": "AAPL",
                "fiscalYear": "2024",
                "date": "2024-09-28",
                "reportedCurrency": "USD",
                "revenue": 900,
                "operatingIncome": 250,
                "netIncome": 180,
            },
        ],
        "balance_sheets": [
            {
                "symbol": "AAPL",
                "fiscalYear": "2025",
                "date": "2025-09-27",
                "reportedCurrency": "USD",
                "cashAndCashEquivalents": 150,
                "totalDebt": 120,
            },
            {
                "symbol": "AAPL",
                "fiscalYear": "2024",
                "date": "2024-09-28",
                "reportedCurrency": "USD",
                "cashAndCashEquivalents": 130,
                "totalDebt": 140,
            },
        ],
        "cash_flow_statements": [
            {
                "symbol": "AAPL",
                "fiscalYear": "2025",
                "date": "2025-09-27",
                "reportedCurrency": "USD",
                "operatingCashFlow": 260,
                "capitalExpenditure": -60,
            },
            {
                "symbol": "AAPL",
                "fiscalYear": "2024",
                "date": "2024-09-28",
                "reportedCurrency": "USD",
                "operatingCashFlow": 230,
                "capitalExpenditure": -50,
            },
        ],
    }


def create_dataset(
    *,
    provider: str = "fmp",
    ticker: str = "AAPL",
    payloads: dict[str, object] | None = None,
) -> RawFinancialDataset:
    """Crete a raw FMP dataset for test."""

    return RawFinancialDataset(
        provider=provider,
        ticker=ticker,
        collected_at=COLLECTION_TIME,
        payloads=payloads or create_payloads(),
    )


def get_records(
    payloads: dict[str, object],
    payload_name: str,
) -> list[PayloadRecord]:
    """Return a mutable paylaod list for test setup."""

    return cast(
        list[PayloadRecord],
        payloads[payload_name],
    )


def test_normalize_fmp_dataset_creates_domain_models() -> None:
    result = normalize_fmp_dataset(create_dataset())

    assert result.metadata.as_of_date.isoformat() == "2025-09-27"
    assert result.metadata.currency == "USD"
    assert result.metadata.source == "Financial Modeling Prep"

    assert result.company.ticker == "AAPL"
    assert result.company.name == "Apple Inc."
    assert result.company.sector == "Technology"
    assert result.company.industry == "Consumer Electronics"

    assert [financial.fiscal_year for financial in result.annual_financials] == [
        2024,
        2025,
    ]

    latest = result.annual_financials[-1]

    assert latest.revenue == 1000
    assert latest.operating_income == 300
    assert latest.net_income == 200
    assert latest.cash_and_equivalents == 150
    assert latest.total_debt == 120
    assert latest.operating_cash_flow == 260

    # FMP commonly represents capital expenditure as a cash outflow.
    # our domain model stores the positive amount spent.
    assert latest.capital_expenditures == 60


def test_normalizer_accepts_calendar_year_field() -> None:
    payloads = create_payloads()

    for payload_name in (
        "income_statements",
        "balance_sheets",
        "cash_flow_statements",
    ):
        for record in get_records(payloads, payload_name):
            record["calendarYear"] = record.pop("fiscalYear")

    result = normalize_fmp_dataset(create_dataset(payloads=payloads))

    assert [financial.fiscal_year for financial in result.annual_financials] == [
        2024,
        2025,
    ]


def test_normalizer_rejects_wrong_provider() -> None:
    dataset = create_dataset(provider="another-provider")

    with pytest.raises(
        NormalizationError,
        match="received data from provider",
    ):
        normalize_fmp_dataset(dataset)


def test_normalizer_rejects_empty_ticker() -> None:
    dataset = create_dataset(ticker="  ")

    with pytest.raises(
        NormalizationError,
        match="empty ticker",
    ):
        normalize_fmp_dataset(dataset)


def test_normalizer_rejects_missing_payload() -> None:
    payloads = create_payloads()
    del payloads["balance_sheets"]

    with pytest.raises(
        NormalizationError,
        match="balance_sheets.*missing",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_non_array_payload() -> None:
    payloads = create_payloads()
    payloads["income_statements"] = {}

    with pytest.raises(
        NormalizationError,
        match="must be a JSON array",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_empty_profile() -> None:
    payloads = create_payloads()
    payloads["profile"] = []

    with pytest.raises(
        NormalizationError,
        match="profile.*must not be empty",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_none_object_record() -> None:
    payloads = create_payloads()
    payloads["profile"] = ["invalid"]

    with pytest.raises(
        NormalizationError,
        match="must be a JSON object",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_duplicate_fiscal_year() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    income_records.append(dict(income_records[0]))

    with pytest.raises(
        NormalizationError,
        match="duplicate fiscal year 2025",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_mismatched_year_coverage() -> None:
    payloads = create_payloads()
    get_records(
        payloads,
        "cash_flow_statements",
    ).pop()

    with pytest.raises(
        NormalizationError,
        match="fiscal-year coverage does not match",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_mismatched_reporting_dates() -> None:
    payloads = create_payloads()
    balance_records = get_records(
        payloads,
        "balance_sheets",
    )
    balance_records[0]["date"] = "2025-09-26"

    with pytest.raises(
        NormalizationError,
        match="reporting dates do not match",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_wrong_statement_ticker() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    income_records[0]["symbol"] = "MSFT"

    with pytest.raises(
        NormalizationError,
        match="MSFT.*AAPL",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_currency_mismatch() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    income_records[0]["reportedCurrency"] = "CAD"

    with pytest.raises(
        NormalizationError,
        match="CAD.*USD",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_missing_financial_field() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    del income_records[0]["operatingIncome"]

    with pytest.raises(
        NormalizationError,
        match="operatingIncome.*missing",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_non_integer_financial_value() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    income_records[0]["revenue"] = 1000.25

    with pytest.raises(
        NormalizationError,
        match="revenue.*must be an integer",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))


def test_normalizer_rejects_conflicting_year_fields() -> None:
    payloads = create_payloads()
    income_records = get_records(
        payloads,
        "income_statements",
    )
    income_records[0]["calendarYear"] = "2024"

    with pytest.raises(
        NormalizationError,
        match="conflicting fiscal-year values",
    ):
        normalize_fmp_dataset(create_dataset(payloads=payloads))

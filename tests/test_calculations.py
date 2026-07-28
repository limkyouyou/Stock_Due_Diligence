"""Tests for financial calculations."""

import pytest

from stock_dd.calculations import (
    calculate_annual_metrics,
    calculate_free_cash_flow,
    calculate_operating_margin,
    calculate_percentage_change,
)
from stock_dd.models import AnnualFinancial


def create_financial(
        *,
        fiscal_year: int = 2025,
        revenue: int = 160_000_000,
        operating_income: int = 18_000_000,
        operating_cash_flow: int = 24_000_000,
        capital_expenditures: int = 7_000_000,
) -> AnnualFinancial:
    """Create an AnnualFinancial object for testing."""

    return AnnualFinancial(
        fiscal_year=fiscal_year,
        revenue=revenue,
        operating_income=operating_income,
        net_income=12_000_000,
        cash_and_equivalents=31_000_000,
        total_debt=24_000_000,
        operating_cash_flow=operating_cash_flow,
        capital_expenditures=capital_expenditures,
    )


def test_calculate_percentage_chage() -> None:
    result = calculate_percentage_change(
        current_value=138_000_000,
        previous_value=120_000_000,
    )

    assert result == pytest.approx(15.0)


def test_percentage_chage_returns_none_for_zero_previous_value() -> None:
    result = calculate_percentage_change(
        current_value=10,
        previous_value=0,
    )

    assert result is None


def test_calculate_operating_margin() -> None:
    financial = create_financial()

    result = calculate_operating_margin(financial)

    assert result == pytest.approx(11.25)


def test_operating_margin_returns_none_for_zero_revenue() -> None:
    financial = create_financial(
        revenue=0,
        operating_income=0,
    )

    result = calculate_operating_margin(financial)

    assert result is None


def test_calculate_free_cash_flow() -> None:
    financial = create_financial()

    result = calculate_free_cash_flow(financial)

    assert result == 17_000_000


def test_calculate_annual_metrics_in_chronological_order() -> None:
    financials = (
        create_financial(
            fiscal_year=2025,
            revenue=160_000_000,
            operating_income=18_000_000,
            operating_cash_flow=24_000_000,
            capital_expenditures=7_000_000,
        ),
        create_financial(
            fiscal_year=2023,
            revenue=120_000_000,
            operating_income=10_000_000,
            operating_cash_flow=14_000_000,
            capital_expenditures=5_000_000,
        ),
        create_financial(
            fiscal_year=2024,
            revenue=138_000_000,
            operating_income=13_000_000,
            operating_cash_flow=18_000_000,
            capital_expenditures=6_000_000,
        ),
    )

    results = calculate_annual_metrics(financials)

    assert [result.fiscal_year for result in results] == [
        2023,
        2024,
        2025,
    ]

    assert results[0].revenue_growth_percent is None
    assert results[1].revenue_growth_percent == pytest.approx(15.0)
    assert results[2].revenue_growth_percent == pytest.approx(15.9420289855)

    assert results[0].free_cash_flow == 9_000_000
    assert results[1].free_cash_flow == 12_000_000
    assert results[2].free_cash_flow == 17_000_000
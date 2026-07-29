"""Deterministic financial calculations for stock reserach."""

from collections.abc import Sequence
from dataclasses import dataclass

from stock_dd.models import AnnualFinancial


@dataclass(frozen=True, slots=True)
class AnnualFinancialMetrics:
    """Calculated metrics for one fiscal year."""

    fiscal_year: int
    revenue_growth_percent: float | None
    operating_margin_percent: float | None
    free_cash_flow: int


def calculate_percentage_change(
    current_value: int | float,
    previous_value: int | float,
) -> float | None:
    """Calculate percentage change from a previous value.

    Reutrns None when the previous value is zero because percentage change would be undefined.
    """

    if previous_value == 0:
        return None

    return (current_value - previous_value) / abs(previous_value) * 100


def calculate_operating_margin(
    financial: AnnualFinancial,
) -> float | None:
    """Calculate operating income as a percentage of revenue."""

    if financial.revenue == 0:
        return None

    return financial.operating_income / financial.revenue * 100


def calculate_free_cash_flow(financial: AnnualFinancial) -> int:
    """Calculate free cash flow.

    Capital expenditures use the project's positive-value convention
    """

    return financial.operating_cash_flow - financial.capital_expenditures


def calculate_annual_metrics(
    financials: Sequence[AnnualFinancial],
) -> tuple[AnnualFinancialMetrics, ...]:
    """Calculate metrics for each fiscal year in chronological order."""

    ordered_financials = sorted(
        financials,
        key=lambda financial: financial.fiscal_year,
    )

    metrics: list[AnnualFinancialMetrics] = []
    previous_financial: AnnualFinancial | None = None

    for financial in ordered_financials:
        revenue_growth = None

        if previous_financial is not None:
            revenue_growth = calculate_percentage_change(
                current_value=financial.revenue,
                previous_value=previous_financial.revenue,
            )

        metrics.append(
            AnnualFinancialMetrics(
                fiscal_year=financial.fiscal_year,
                revenue_growth_percent=revenue_growth,
                operating_margin_percent=calculate_operating_margin(financial),
                free_cash_flow=calculate_free_cash_flow(financial),
            )
        )

        previous_financial = financial

    return tuple(metrics)

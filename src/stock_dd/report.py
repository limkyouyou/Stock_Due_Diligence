"""Generate Markdown reports from normalized stock research data."""

from collections.abc import Sequence
from pathlib import Path

from stock_dd.calculations import AnnualFinancialMetrics
from stock_dd.models import CompanyResearchData

def generate_markdown_report(
        research_data: CompanyResearchData,
        metrics: Sequence[AnnualFinancialMetrics],
) -> str:
    """Generate a markdown due-diligence report."""

    metrics_by_year = {metric.fiscal_year: metric for metric in metrics}

    if len(metrics_by_year) != len(metrics):
        raise ValueError(
            "Calculated metrics contain duplicate fiscal years."
        )

    ordered_financials = sorted(
        research_data.annual_financials, key=lambda financial: financial.fiscal_year,
    )

    missing_years = [
        financial.fiscal_year
        for financial in ordered_financials
        if financial.fiscal_year not in metrics_by_year
    ]

    if missing_years:
        missing = ", ".join(str(year) for year in missing_years)
        raise ValueError(
            f"Calculated metrics are missing fiscal years: {missing}."
        )

    company = research_data.company
    metadata = research_data.metadata
    currency = metadata.currency

    lines = [
        (
            "# Stock Due-Diligence Report: "
            f"{company.name} ({company.ticker})"
        ),
        "",
        "## Research Information",
        "",
        f"- **As-of date:** {metadata.as_of_date.isoformat()}",
        f"- **Currency:** {currency}",
        f"- **Data source:** {metadata.source}",
        "",
        "## Company Overview",
        "",
        f"- **Sector:** {company.sector}",
        f"- **Industry:** {company.industry}",
        "",
        company.description,
        "",
        "## Annual Financial Summary",
        "",
        (
            "| Fiscal Year | Revenue | Revenue Growth "
            "| Operating Margin | Free Cash Flow |"
        ),
        "|---:|---:|---:|---:|---:|",
    ]

    for financial in ordered_financials:
        year_metrics = metrics_by_year[financial.fiscal_year]

        lines.append(
            f"| {financial.fiscal_year} "
            f"| {_format_money(financial.revenue, currency)} "
            f"| {_format_percentage(year_metrics.revenue_growth_percent)} "
            f"| {_format_percentage(year_metrics.operating_margin_percent)} "
            f"| {_format_money(year_metrics.free_cash_flow, currency)} |"
        ) 

    latest_financial = ordered_financials[-1]
    latest_metrics = metrics_by_year[latest_financial.fiscal_year]

    lines.extend(
        [
            "",
            f"## Latest Fiscal Year: {latest_financial.fiscal_year}",
            "",
            (
                "- **Operating income:** "
                f"{_format_money(latest_financial.operating_income, currency)}"
            ),
            (
                "- **Net income:** "
                f"{_format_money(latest_financial.net_income, currency)}"
            ),
            (
                "- **Cash and equivalents:** "
                f"{_format_money(
                    latest_financial.cash_and_equivalents,
                    currency,
                )}"
            ),
            (
                "- **Total debt:** "
                f"{_format_money(latest_financial.total_debt, currency)}"
            ),
            (
                "- **Free cash flow:** "
                f"{_format_money(
                    latest_metrics.free_cash_flow,
                    currency,
                )}"
            ),
            "",
            "## Scope and Limitations",
            "",
            (
                "This offline prototype uses only the supplied sample "
                "financial data."
            ),
            (
                "It does not yet include market prices, valuation metrics, "
                "company news, filings, forecasts, or AI-generated analysis."
            ),
            (
                "The report is intended to support human research and does "
                "not provide a buy or sell recommendation."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def save_markdown_report(
        report: str,
        output_path: str | Path,
) -> Path:
    """Save a Markdown report and return its path."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        report,
        encoding="utf-8",
        newline="\n",
    )

    return path


def _format_money(
        value: int | float,
        currency: str,
) -> str:
    """Format a monetary value with its currency code."""

    return f"{currency} {value:,.0f}"


def _format_percentage(value: float | None) -> str:
    """format a percentage or show that it is unavailable"""

    if value is None:
        return "N/A"

    return f"{value:.2f}%"
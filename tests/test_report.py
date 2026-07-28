"""Tests for Markdown report generation."""

from datetime import date
from pathlib import Path

from stock_dd.calculations import calculate_annual_metrics
from stock_dd.models import (
    AnnualFinancial,
    Company,
    CompanyResearchData,
    ResearchMetadata,
)
from stock_dd.report import (
    generate_markdown_report,
    save_markdown_report,
)


def create_research_data() -> CompanyResearchData:
    """Create normalized research data for report tests."""

    return CompanyResearchData(
        metadata=ResearchMetadata(
            as_of_date=date(2025, 12, 31),
            currency="USD",
            source="Report test data",
        ),
        company=Company(
            ticker="NSTR",
            name="Northstar Robotics Inc.",
            sector="Industrials",
            industry="Industrial Automation",
            description="A fictional robotics company.",
        ),
        annual_financials=(
            AnnualFinancial(
                fiscal_year=2024,
                revenue=138_000_000,
                operating_income=13_000_000,
                net_income=8_000_000,
                cash_and_equivalents=25_000_000,
                total_debt=28_000_000,
                operating_cash_flow=18_000_000,
                capital_expenditures=6_000_000,
            ),
            AnnualFinancial(
                fiscal_year=2025,
                revenue=160_000_000,
                operating_income=18_000_000,
                net_income=12_000_000,
                cash_and_equivalents=31_000_000,
                total_debt=24_000_000,
                operating_cash_flow=24_000_000,
                capital_expenditures=7_000_000,
            ),
        ),
    )


def test_generate_markdown_report_contains_financial_summary() -> None:
    research_data = create_research_data()
    metrics = calculate_annual_metrics(
        research_data.annual_financials
    )

    report = generate_markdown_report(
        research_data,
        metrics,
    )

    assert (
        "# Stock Due-Diligence Report: "
        "Northstar Robotics Inc. (NSTR)"
    ) in report

    assert (
        "| 2025 | USD 160,000,000 | 15.94% "
        "| 11.25% | USD 17,000,000 |"
    ) in report

    assert "## Scope and Limitations" in report
    assert "buy or sell recommendation" in report


def test_save_markdown_report_creates_output_directory(
        tmp_path: Path,
) -> None:
    output_path = tmp_path / "nested" / "report.md"

    saved_path = save_markdown_report(
        "# Test Report\n",
        output_path
    )

    assert saved_path == output_path
    assert output_path.exists()
    assert output_path.read_text(
        encoding="utf-8"
    ) == "# Test Report\n"
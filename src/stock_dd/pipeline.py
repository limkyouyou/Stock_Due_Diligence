"""Coordinate the offline stock due-diligence pipeline"""

from dataclasses import dataclass
from pathlib import Path

from stock_dd.calculations import calculate_annual_metrics
from stock_dd.loader import load_research_data
from stock_dd.report import (
    generate_markdown_report,
    save_markdown_report,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Result of a complete offline pipeline run."""

    input_path: Path
    output_path: Path
    company_ticker: str


def run_offline_pipeline(
        input_path: str | Path,
        output_path: str | Path | None = None,
) -> PipelineResult:
    """Run the complete offline due-diligence workflow."""

    source_path = Path(input_path)

    research_data = load_research_data(source_path)

    metrics = calculate_annual_metrics(research_data.annual_financials)

    report = generate_markdown_report(
        research_data,
        metrics,
    )

    if output_path is None:
        report_filename = (
            f"{research_data.company.ticker.lower()}_"
            f"{research_data.metadata.as_of_data.isoformat()}_report.md"
        )
        destination_path = Path("reports") / report_filename
    else:
        destination_path = Path(output_path)

    saved_path = save_markdown_report(
        report,
        destination_path,
    )

    return PipelineResult(
        input_path=source_path,
        output_path=saved_path,
        company_ticker=research_data.company.ticker,
    )
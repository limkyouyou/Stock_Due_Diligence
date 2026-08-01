"""Coordinate the offline stock due-diligence pipeline"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from stock_dd.calculations import calculate_annual_metrics
from stock_dd.collectors.base import (
    FinancialDataCollector,
    RawFinancialDataset,
)
from stock_dd.loader import load_research_data
from stock_dd.models import CompanyResearchData
from stock_dd.report import (
    generate_markdown_report,
    save_markdown_report,
)
from stock_dd.storage.raw_data import save_raw_financial_dataset

type FinancialDataNormalizer = Callable[
    [RawFinancialDataset],
    CompanyResearchData,
]


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LivePipelineResult:
    """Result of a completed live financial-data pipeline."""

    provider: str
    company_ticker: str
    raw_data_path: Path
    report_path: Path


def run_live_pipeline(
    ticker: str,
    *,
    collector: FinancialDataCollector,
    normalizer: FinancialDataNormalizer,
    raw_data_directory: str | Path,
    output_path: str | Path | None = None,
    annual_limit: int = 5,
) -> LivePipelineResult:
    """Collect live financial data and generate a report."""

    logger.info(
        "Starting live pipeline: provider=%s, ticker=%s",
        collector.provider_name,
        ticker,
    )

    raw_dataset = collector.collect(
        ticker,
        annual_limit=annual_limit,
    )

    raw_data_path = save_raw_financial_dataset(
        raw_dataset,
        raw_data_directory,
    )

    logger.info(
        "Saved raw provider data: path=%s",
        raw_data_path,
    )

    research_data = normalizer(raw_dataset)

    metrics = calculate_annual_metrics(research_data.annual_financials)

    report = generate_markdown_report(
        research_data,
        metrics,
    )

    if output_path is None:
        report_filename = (
            f"{research_data.company.ticker.lower()}_"
            f"{research_data.metadata.as_of_date.isoformat()}_report.md"
        )
        destination_path = Path("reports") / report_filename
    else:
        destination_path = Path(output_path)

    report_path = save_markdown_report(
        report,
        destination_path,
    )

    logger.info(
        "Completed live pipeline: ticker=%s, report=%s",
        research_data.company.ticker,
        report_path,
    )

    return LivePipelineResult(
        provider=raw_dataset.provider,
        company_ticker=research_data.company.ticker,
        raw_data_path=raw_data_path,
        report_path=report_path,
    )


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Result of a completed offline pipeline run."""

    input_path: Path
    output_path: Path
    company_ticker: str


def run_offline_pipeline(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> PipelineResult:
    """Run the complete offline due-diligence workflow."""

    source_path = Path(input_path)

    logger.info(
        "Starting offline pipeline: input=%s",
        source_path,
    )

    research_data = load_research_data(source_path)

    logger.info(
        "Loaded research data: ticker=%s, fiscal_years=%d",
        research_data.company.ticker,
        len(research_data.annual_financials),
    )

    metrics = calculate_annual_metrics(research_data.annual_financials)

    report = generate_markdown_report(
        research_data,
        metrics,
    )

    if output_path is None:
        report_filename = (
            f"{research_data.company.ticker.lower()}_"
            f"{research_data.metadata.as_of_date.isoformat()}_report.md"
        )
        destination_path = Path("reports") / report_filename
    else:
        destination_path = Path(output_path)

    saved_path = save_markdown_report(
        report,
        destination_path,
    )

    logger.info(
        "Saved due-diligence report: output=%s",
        saved_path,
    )

    return PipelineResult(
        input_path=source_path,
        output_path=saved_path,
        company_ticker=research_data.company.ticker,
    )

"""Integration tests for the offline research pipeline."""

import json
from datetime import UTC, datetime
from pathlib import Path

from stock_dd.collectors.base import (
    FinancialDataCollector,
    RawFinancialDataset,
)
from stock_dd.normalizers.fmp import normalize_fmp_dataset
from stock_dd.pipeline import (
    run_live_pipeline,
    run_offline_pipeline,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_FILE = PROJECT_ROOT / "data" / "samples" / "northstar_robotics.json"


def test_run_offline_pipeline_creates_report(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "northstar_report.md"

    result = run_offline_pipeline(
        input_path=SAMPLE_FILE,
        output_path=output_path,
    )

    assert result.company_ticker == "NSTR"
    assert result.output_path == output_path
    assert output_path.exists()

    report = output_path.read_text(encoding="utf-8")

    assert "Northstar Robotics Inc." in report
    assert "USD 160,000,000" in report
    assert "15.94%" in report
    assert "USD 17,000,000" in report


class FakeFinancialCollector:
    """Return predictable provider data without network access."""

    def __init__(self, dataset: RawFinancialDataset) -> None:
        self._dataset = dataset
        self.received_ticker: str | None = None
        self.received_annual_limit: int | None = None

    @property
    def provider_name(self) -> str:
        return "fmp"

    def collect(
        self,
        ticker: str,
        *,
        annual_limit: int = 5,
    ) -> RawFinancialDataset:
        self.received_ticker = ticker
        self.received_annual_limit = annual_limit
        return self._dataset


def create_raw_fmp_dataset() -> RawFinancialDataset:
    """Create synthetic raw RMP data for pipeline testing."""

    return RawFinancialDataset(
        provider="fmp",
        ticker="AAPL",
        collected_at=datetime(
            2026,
            8,
            1,
            20,
            0,
            tzinfo=UTC,
        ),
        payloads={
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
                }
            ],
            "balance_sheets": [
                {
                    "symbol": "AAPL",
                    "fiscalYear": "2025",
                    "date": "2025-09-27",
                    "reportedCurrency": "USD",
                    "cashAndCashEquivalents": 150,
                    "totalDebt": 120,
                }
            ],
            "cash_flow_statements": [
                {
                    "symbol": "AAPL",
                    "fiscalYear": "2025",
                    "date": "2025-09-27",
                    "reportedCurrency": "USD",
                    "operatingCashFlow": 260,
                    "capitalExpenditure": -60,
                }
            ],
        },
    )


def test_run_live_pipeline_saves_raw_data_and_report(
    tmp_path: Path,
) -> None:
    dataset = create_raw_fmp_dataset()
    collector = FakeFinancialCollector(dataset)

    typed_collector: FinancialDataCollector = collector

    raw_directory = tmp_path / "raw"
    report_path = tmp_path / "reports" / "aapl.md"

    result = run_live_pipeline(
        "aapl",
        collector=typed_collector,
        normalizer=normalize_fmp_dataset,
        raw_data_directory=raw_directory,
        output_path=report_path,
        annual_limit=3,
    )

    assert collector.received_ticker == "aapl"
    assert collector.received_annual_limit == 3

    assert result.provider == "fmp"
    assert result.company_ticker == "AAPL"
    assert result.report_path == report_path

    assert result.raw_data_path.exists()
    assert result.report_path.exists()

    raw_envelope = json.loads(result.raw_data_path.read_text(encoding="utf-8"))

    assert raw_envelope["provider"] == "fmp"
    assert raw_envelope["ticker"] == "AAPL"

    report = report_path.read_text(encoding="utf-8")

    assert "Apple Inc. (AAPL)" in report
    assert "USD 1,000" in report
    assert "USD 200" in report
